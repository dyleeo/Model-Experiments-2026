/**
 * YOLOv8 ONNX inference in the browser.
 * Expects model at /models/yolov8n.onnx (export: yolo export model=yolov8n.pt format=onnx).
 * Input: 1x3x640x640, RGB, 0-1 normalized. Output: 1x84x8400 (4 box + 80 classes).
 */

const INPUT_SIZE = 640;
const NUM_CLASSES = 80;

/** Full COCO class names in YOLO order (index 0 = person). */
export const COCO_CLASSES = [
	'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
	'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog',
	'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella',
	'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite',
	'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle',
	'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich',
	'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
	'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote',
	'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book',
	'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
];

let session = null;

/**
 * Load ONNX session. Prefer WebGPU, fallback to WASM.
 * @param {string} modelId - e.g. 'yolov8n'
 * @param {string} [basePath=''] - SvelteKit base path (e.g. '' or '/app') so the model URL is correct
 * @returns {Promise<boolean>} true if loaded
 */
export async function loadModel(modelId = 'yolov8n', basePath = '') {
	if (session) {
		try {
			session.release?.();
		} catch (_) {}
		session = null;
	}

	const ort = await import('onnxruntime-web');

	// Point WASM loader to our static files so ort-wasm-simd-threaded.wasm/.mjs can be fetched (fixes "fetching of the wasm failed")
	const base = (typeof basePath === 'string' && basePath) ? basePath.replace(/\/$/, '') : '';
	if (typeof ort.env !== 'undefined' && ort.env.wasm && typeof window !== 'undefined' && window.location?.origin) {
		const wasmDir = `${base}/onnxruntime-wasm/`;
		ort.env.wasm.wasmPaths = new URL(wasmDir, window.location.origin).href;
	}

	// Prefer WebGPU (much faster); fallback to WASM if WebGPU unavailable or fails
	const providers = [];
	if (typeof navigator !== 'undefined' && navigator.gpu) {
		try {
			const adapter = await navigator.gpu.requestAdapter();
			if (adapter) providers.push('webgpu');
		} catch (_) {}
	}
	providers.push('wasm');
	// Same-origin URL for the model file (static folder) and API fallback (when static isn't served)
	const staticPath = `${base}/models/${modelId}.onnx`;
	const staticUrl = typeof window !== 'undefined' && window.location?.origin
		? new URL(staticPath, window.location.origin).href
		: staticPath;
	const apiPath = `${base}/api/yolo-model/${modelId}`;
	const apiUrl = typeof window !== 'undefined' && window.location?.origin
		? new URL(apiPath, window.location.origin).href
		: apiPath;

	let res = await fetch(staticUrl);
	if (!res.ok) {
		// Fallback: server route that reads from static/models (helps when static isn't served at /)
		res = await fetch(apiUrl);
	}
	if (!res.ok) {
		const err = new Error(`Model not found: ${res.status}. Tried ${staticUrl} and ${apiUrl}`);
		err.status = res.status;
		throw err;
	}
	const buf = await res.arrayBuffer();
	session = await ort.InferenceSession.create(buf, {
		executionProviders: providers,
		graphOptimizationLevel: 'all'
	});
	return true;
}

/**
 * Preprocess video frame to 1x3x640x640 RGB float32 (0-1), NCHW.
 * Uses a temporary canvas; preserves aspect ratio by letterboxing (black bars).
 * @param {HTMLVideoElement} video
 * @returns {{ tensor: Float32Array, scale: number, padX: number, padY: number, origW: number, origH: number }}
 */
export function preprocess(video) {
	const origW = video.videoWidth;
	const origH = video.videoHeight;
	const scale = Math.min(INPUT_SIZE / origW, INPUT_SIZE / origH);
	const scaledW = Math.round(origW * scale);
	const scaledH = Math.round(origH * scale);
	const padX = (INPUT_SIZE - scaledW) / 2;
	const padY = (INPUT_SIZE - scaledH) / 2;

	const canvas = document.createElement('canvas');
	canvas.width = INPUT_SIZE;
	canvas.height = INPUT_SIZE;
	const ctx = canvas.getContext('2d');
	ctx.fillStyle = 'black';
	ctx.fillRect(0, 0, INPUT_SIZE, INPUT_SIZE);
	ctx.drawImage(video, 0, 0, origW, origH, padX, padY, scaledW, scaledH);

	const imageData = ctx.getImageData(0, 0, INPUT_SIZE, INPUT_SIZE);
	const data = imageData.data;
	const tensor = new Float32Array(1 * 3 * INPUT_SIZE * INPUT_SIZE);
	const size = INPUT_SIZE * INPUT_SIZE;
	for (let i = 0; i < size; i++) {
		tensor[i] = data[i * 4] / 255;         // R
		tensor[size + i] = data[i * 4 + 1] / 255;   // G
		tensor[2 * size + i] = data[i * 4 + 2] / 255; // B
	}
	return { tensor, scale, padX, padY, origW, origH, scaledW, scaledH };
}

function sigmoid(x) {
	return 1 / (1 + Math.exp(-x));
}

/**
 * Non-maximum suppression by IoU.
 * @param {{ bbox: number[], class: number, confidence: number }[]} boxes
 * @param {number} iouThreshold
 */
function nms(boxes, iouThreshold = 0.45) {
	boxes.sort((a, b) => b.confidence - a.confidence);
	const out = [];
	while (boxes.length) {
		const top = boxes.shift();
		out.push(top);
		for (let i = boxes.length - 1; i >= 0; i--) {
			if (boxes[i].class !== top.class) continue;
			if (iou(boxes[i].bbox, top.bbox) > iouThreshold) boxes.splice(i, 1);
		}
	}
	return out;
}

function iou(a, b) {
	const [ax1, ay1, ax2, ay2] = a;
	const [bx1, by1, bx2, by2] = b;
	const interX1 = Math.max(ax1, bx1);
	const interY1 = Math.max(ay1, by1);
	const interX2 = Math.min(ax2, bx2);
	const interY2 = Math.min(ay2, by2);
	const interW = Math.max(0, interX2 - interX1);
	const interH = Math.max(0, interY2 - interY1);
	const inter = interW * interH;
	const areaA = (ax2 - ax1) * (ay2 - ay1);
	const areaB = (bx2 - bx1) * (by2 - by1);
	return inter / (areaA + areaB - inter);
}

/**
 * Run YOLOv8 detection on a video frame. Handles preprocessing, inference, and postprocessing.
 * @param {HTMLVideoElement} video
 * @param {number} confidenceThreshold
 * @returns {Promise<{ detections: { class: string, confidence: number, bbox: { x, y, width, height } }[], inferenceMs: number }>}
 */
export async function detect(video, confidenceThreshold = 0.5) {
	if (!session || !video?.videoWidth) {
		return { detections: [], inferenceMs: 0 };
	}
	const t0 = performance.now();
	const { tensor, ...meta } = preprocess(video);
	const ort = await import('onnxruntime-web');
	const inputName = session.inputNames[0];
	const feeds = { [inputName]: new ort.Tensor('float32', tensor, [1, 3, INPUT_SIZE, INPUT_SIZE]) };
	const output = await session.run(feeds);
	const raw = output[session.outputNames[0]];
	const inferenceMs = Math.round(performance.now() - t0);
	const detections = postprocessFromRaw(raw, meta, confidenceThreshold);
	return { detections, inferenceMs };
}

/** Postprocess from raw ONNX output. Handles (1, 84, 8400) or (1, 8400, 84) layout. */
function postprocessFromRaw(raw, preprocessMeta, confidenceThreshold) {
	const [_, d1, d2] = raw.dims;
	// YOLOv8 outputs (1, 84, 8400): channels=84, predictions=8400. Or (1, 8400, 84) in some exports.
	const numChannels = Math.min(d1, d2);
	const numPredictions = Math.max(d1, d2);
	const data = raw.data;
	const { scale, padX, padY, origW, origH, scaledW, scaledH } = preprocessMeta;
	const candidates = [];

	// Inverse scale from 640x640 letterbox space to original image (use actual scaled size so alignment is exact)
	const scaleX = scaledW > 0 ? origW / scaledW : 1;
	const scaleY = scaledH > 0 ? origH / scaledH : 1;

	// Layout (1, 84, 8400): index = channel * numPredictions + i
	const channelFirst = d1 === numChannels;
	const stride = channelFirst ? numPredictions : numChannels;

	for (let i = 0; i < numPredictions; i++) {
		const cx = channelFirst ? data[0 * stride + i] : data[i * stride + 0];
		const cy = channelFirst ? data[1 * stride + i] : data[i * stride + 1];
		const w = channelFirst ? data[2 * stride + i] : data[i * stride + 2];
		const h = channelFirst ? data[3 * stride + i] : data[i * stride + 3];

		let maxScore = 0;
		let maxClass = 0;
		for (let c = 0; c < NUM_CLASSES; c++) {
			const s = sigmoid(
				channelFirst ? data[(4 + c) * stride + i] : data[i * stride + 4 + c]
			);
			if (s > maxScore) {
				maxScore = s;
				maxClass = c;
			}
		}
		if (maxScore < confidenceThreshold) continue;

		// Map from 640 letterbox coords to original image using exact inverse of drawImage scale
		const cxOrig = (cx - padX) * scaleX;
		const cyOrig = (cy - padY) * scaleY;
		const wOrig = w * scaleX;
		const hOrig = h * scaleY;
		const x1 = Math.max(0, cxOrig - wOrig / 2);
		const y1 = Math.max(0, cyOrig - hOrig / 2);
		const x2 = Math.min(origW, cxOrig + wOrig / 2);
		const y2 = Math.min(origH, cyOrig + hOrig / 2);

		candidates.push({
			bbox: [x1, y1, x2, y2],
			class: maxClass,
			confidence: maxScore
		});
	}

	const kept = nms(candidates, 0.45);
	return kept.map(({ bbox, class: cls, confidence }) => ({
		class: COCO_CLASSES[cls] ?? 'unknown',
		confidence,
		bbox: {
			x: bbox[0],
			y: bbox[1],
			width: bbox[2] - bbox[0],
			height: bbox[3] - bbox[1]
		}
	}));
}

export function isLoaded() {
	return !!session;
}
