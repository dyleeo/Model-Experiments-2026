<script>
	import { onMount } from 'svelte';

	// Model state
	let modelLoaded = $state(false);
	let isLoadingModel = $state(false);
	let modelError = $state(null);
	let webgpuSupported = $state(null);
	let selectedModel = $state('yolov8n'); // n, s, m, l, x

	// Video/webcam state
	let videoRef = $state(null);
	let canvasRef = $state(null);
	let isStreaming = $state(false);
	let useWebcam = $state(false);

	// Detection state
	let detections = $state([]);
	let fps = $state(0);
	let inferenceTime = $state(0);
	let isDetecting = $state(false);

	// Settings
	let confidenceThreshold = $state(0.5);
	let showLabels = $state(true);
	let showSegmentation = $state(true);

	const modelSizes = [
		{ id: 'yolov8n', name: 'YOLOv8n', size: '6MB', speed: 'Fastest' },
		{ id: 'yolov8s', name: 'YOLOv8s', size: '22MB', speed: 'Fast' },
		{ id: 'yolov8m', name: 'YOLOv8m', size: '50MB', speed: 'Medium' },
		{ id: 'yolov8l', name: 'YOLOv8l', size: '87MB', speed: 'Slower' }
	];

	// COCO classes (subset for display)
	const cocoClasses = [
		'person',
		'bicycle',
		'car',
		'motorcycle',
		'airplane',
		'bus',
		'train',
		'truck',
		'boat',
		'traffic light',
		'fire hydrant',
		'stop sign',
		'parking meter',
		'bench',
		'bird',
		'cat',
		'dog',
		'horse',
		'sheep',
		'cow'
	];

	onMount(async () => {
		// Check WebGPU support
		if ('gpu' in navigator) {
			try {
				const adapter = await navigator.gpu.requestAdapter();
				webgpuSupported = !!adapter;
			} catch {
				webgpuSupported = false;
			}
		} else {
			webgpuSupported = false;
		}
	});

	async function loadModel() {
		isLoadingModel = true;
		modelError = null;

		try {
			// Simulated model loading - in production this would load ONNX model
			await new Promise((resolve) => setTimeout(resolve, 1500));
			modelLoaded = true;
		} catch (e) {
			modelError = e.message;
		} finally {
			isLoadingModel = false;
		}
	}

	async function startWebcam() {
		try {
			const stream = await navigator.mediaDevices.getUserMedia({
				video: { width: 640, height: 480, facingMode: 'environment' }
			});
			if (videoRef) {
				videoRef.srcObject = stream;
				await videoRef.play();
				useWebcam = true;
				isStreaming = true;
				startDetectionLoop();
			}
		} catch (e) {
			console.error('Webcam error:', e);
			modelError = 'Failed to access webcam: ' + e.message;
		}
	}

	function stopWebcam() {
		if (videoRef?.srcObject) {
			const tracks = videoRef.srcObject.getTracks();
			tracks.forEach((track) => track.stop());
			videoRef.srcObject = null;
		}
		isStreaming = false;
		useWebcam = false;
		detections = [];
	}

	function handleVideoSelect(event) {
		const file = event.target.files?.[0];
		if (!file || !videoRef) return;

		stopWebcam();
		const url = URL.createObjectURL(file);
		videoRef.src = url;
		videoRef.play();
		useWebcam = false;
		isStreaming = true;
		startDetectionLoop();
	}

	let animationId = null;
	let lastTime = performance.now();
	let frameCount = 0;

	function startDetectionLoop() {
		if (!modelLoaded) return;

		isDetecting = true;

		function detectFrame() {
			if (!isStreaming) {
				isDetecting = false;
				return;
			}

			const now = performance.now();
			frameCount++;

			// Update FPS every second
			if (now - lastTime >= 1000) {
				fps = frameCount;
				frameCount = 0;
				lastTime = now;
			}

			// Simulate detection - in production this would run ONNX inference
			const startInference = performance.now();

			// Generate mock detections
			detections = generateMockDetections();

			inferenceTime = Math.round(performance.now() - startInference);

			// Draw detections on canvas
			drawDetections();

			animationId = requestAnimationFrame(detectFrame);
		}

		detectFrame();
	}

	function generateMockDetections() {
		// Simulate detected objects with random positions
		const numDetections = Math.floor(Math.random() * 3) + 1;
		const results = [];

		for (let i = 0; i < numDetections; i++) {
			results.push({
				class: cocoClasses[Math.floor(Math.random() * cocoClasses.length)],
				confidence: 0.7 + Math.random() * 0.25,
				bbox: {
					x: Math.random() * 400 + 50,
					y: Math.random() * 300 + 50,
					width: 80 + Math.random() * 100,
					height: 80 + Math.random() * 100
				}
			});
		}

		return results.filter((d) => d.confidence >= confidenceThreshold);
	}

	function drawDetections() {
		if (!canvasRef || !videoRef) return;

		const ctx = canvasRef.getContext('2d');
		canvasRef.width = videoRef.videoWidth || 640;
		canvasRef.height = videoRef.videoHeight || 480;

		ctx.clearRect(0, 0, canvasRef.width, canvasRef.height);

		detections.forEach((det, i) => {
			const colors = ['#4facfe', '#f093fb', '#4ade80', '#f59e0b', '#f87171'];
			const color = colors[i % colors.length];

			// Draw bounding box
			ctx.strokeStyle = color;
			ctx.lineWidth = 2;
			ctx.strokeRect(det.bbox.x, det.bbox.y, det.bbox.width, det.bbox.height);

			// Draw segmentation mask (simulated)
			if (showSegmentation) {
				ctx.fillStyle = color + '40'; // 25% opacity
				ctx.fillRect(det.bbox.x, det.bbox.y, det.bbox.width, det.bbox.height);
			}

			// Draw label
			if (showLabels) {
				const label = `${det.class} ${(det.confidence * 100).toFixed(0)}%`;
				ctx.font = '14px sans-serif';
				const textWidth = ctx.measureText(label).width;

				ctx.fillStyle = color;
				ctx.fillRect(det.bbox.x, det.bbox.y - 20, textWidth + 8, 20);

				ctx.fillStyle = 'white';
				ctx.fillText(label, det.bbox.x + 4, det.bbox.y - 6);
			}
		});
	}

	function toggleStream() {
		if (isStreaming) {
			stopWebcam();
			if (animationId) {
				cancelAnimationFrame(animationId);
			}
		}
	}
</script>

<svelte:head>
	<title>YOLOv8 - Model Experiments 2026</title>
</svelte:head>

<main>
	<nav class="breadcrumb">
		<a href="/">← Back to experiments</a>
	</nav>

	<h1>YOLOv8 Detection</h1>
	<p class="subtitle">Real-time object detection & instance segmentation in browser</p>

	<div class="badge-row">
		<span class="badge browser">Browser</span>
		<span class="badge">WebGPU</span>
		<span class="badge">80 COCO Classes</span>
		<span class="badge">Real-time</span>
	</div>

	<!-- WebGPU Status -->
	<div class="status-card">
		{#if webgpuSupported === null}
			<span class="status-indicator checking"></span>
			Checking WebGPU support...
		{:else if webgpuSupported}
			<span class="status-indicator supported"></span>
			WebGPU supported - GPU acceleration available
		{:else}
			<span class="status-indicator unsupported"></span>
			WebGPU not supported - will use WASM fallback
		{/if}
	</div>

	<div class="container">
		<!-- Model Selection -->
		<section class="model-section">
			<h3>Select Model</h3>
			<div class="model-grid">
				{#each modelSizes as model}
					<button
						class="model-option"
						class:active={selectedModel === model.id}
						onclick={() => {
							selectedModel = model.id;
							modelLoaded = false;
						}}
					>
						<span class="model-name">{model.name}</span>
						<span class="model-meta">{model.size} • {model.speed}</span>
					</button>
				{/each}
			</div>

			{#if !modelLoaded}
				<button class="load-btn" onclick={loadModel} disabled={isLoadingModel}>
					{#if isLoadingModel}
						<span class="spinner"></span>
						Loading {selectedModel}...
					{:else}
						Load Model
					{/if}
				</button>
			{:else}
				<div class="model-ready">
					<span class="check">✓</span>
					{selectedModel} loaded
				</div>
			{/if}
		</section>

		{#if modelLoaded}
			<!-- Input Source -->
			<section class="input-section">
				<h3>Input Source</h3>
				<div class="input-buttons">
					<button class="input-btn webcam" onclick={startWebcam} disabled={isStreaming}>
						📷 Start Webcam
					</button>
					<label class="input-btn file">
						<input type="file" accept="video/*" onchange={handleVideoSelect} disabled={isStreaming} />
						📁 Upload Video
					</label>
					{#if isStreaming}
						<button class="input-btn stop" onclick={toggleStream}>⏹ Stop</button>
					{/if}
				</div>
			</section>

			<!-- Settings -->
			<section class="settings-section">
				<div class="setting">
					<label>
						Confidence Threshold: {(confidenceThreshold * 100).toFixed(0)}%
						<input type="range" min="0.1" max="0.9" step="0.05" bind:value={confidenceThreshold} />
					</label>
				</div>
				<div class="setting">
					<label>
						<input type="checkbox" bind:checked={showLabels} />
						Show Labels
					</label>
				</div>
				<div class="setting">
					<label>
						<input type="checkbox" bind:checked={showSegmentation} />
						Show Segmentation
					</label>
				</div>
			</section>

			<!-- Video Display -->
			<section class="video-section">
				<div class="video-container">
					<video bind:this={videoRef} playsinline muted class="video-element">
						<track kind="captions" />
					</video>
					<canvas bind:this={canvasRef} class="detection-overlay"></canvas>

					{#if !isStreaming}
						<div class="video-placeholder">
							<p>Start webcam or upload a video to begin detection</p>
						</div>
					{/if}
				</div>

				<!-- Stats -->
				{#if isStreaming}
					<div class="stats-bar">
						<div class="stat">
							<span class="stat-label">FPS</span>
							<span class="stat-value">{fps}</span>
						</div>
						<div class="stat">
							<span class="stat-label">Inference</span>
							<span class="stat-value">{inferenceTime}ms</span>
						</div>
						<div class="stat">
							<span class="stat-label">Objects</span>
							<span class="stat-value">{detections.length}</span>
						</div>
					</div>
				{/if}

				<!-- Detection List -->
				{#if detections.length > 0}
					<div class="detection-list">
						<h4>Detected Objects</h4>
						<div class="detection-chips">
							{#each detections as det}
								<span class="detection-chip">
									{det.class}
									<small>{(det.confidence * 100).toFixed(0)}%</small>
								</span>
							{/each}
						</div>
					</div>
				{/if}
			</section>
		{/if}

		<!-- Info Section -->
		<section class="info-section">
			<h2>About YOLOv8</h2>
			<div class="info-content">
				<p>
					YOLOv8 is the latest generation of the YOLO (You Only Look Once) family, offering state-of-the-art
					real-time object detection and instance segmentation.
				</p>
				<ul>
					<li><strong>Detection + Segmentation</strong> in a single forward pass</li>
					<li><strong>80 COCO classes</strong> out of the box</li>
					<li><strong>30-300+ FPS</strong> depending on model size and hardware</li>
					<li><strong>Multiple sizes</strong> from nano (6MB) to extra-large (136MB)</li>
				</ul>
			</div>

			<h3>Browser Implementation</h3>
			<div class="code-block">
				<code>
					// Export YOLOv8 to ONNX format<br />
					yolo export model=yolov8n-seg.pt format=onnx<br /><br />
					// Load in browser with ONNX Runtime<br />
					import * as ort from 'onnxruntime-web/webgpu';<br />
					const session = await ort.InferenceSession.create(<br />
					&nbsp;&nbsp;'/models/yolov8n-seg.onnx',<br />
					&nbsp;&nbsp;{'{'} executionProviders: ['webgpu', 'wasm'] {'}'}<br />
					);
				</code>
			</div>
		</section>
	</div>
</main>

<style>
	main {
		max-width: 900px;
		margin: 0 auto;
		padding: 2rem;
	}

	.breadcrumb {
		margin-bottom: 1.5rem;
	}

	.breadcrumb a {
		color: #fa709a;
		text-decoration: none;
		font-size: 0.875rem;
	}

	.breadcrumb a:hover {
		text-decoration: underline;
	}

	h1 {
		font-size: 2.5rem;
		font-weight: 700;
		margin: 0;
		background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}

	.subtitle {
		color: #888;
		margin-top: 0.5rem;
		margin-bottom: 1rem;
	}

	.badge-row {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 1.5rem;
		flex-wrap: wrap;
	}

	.badge {
		background: #2a2a2a;
		color: #888;
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-size: 0.75rem;
		font-weight: 500;
	}

	.badge.browser {
		background: rgba(250, 112, 154, 0.2);
		color: #fa709a;
	}

	.status-card {
		background: #1a1a1a;
		padding: 1rem;
		border-radius: 8px;
		margin-bottom: 1.5rem;
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.status-indicator {
		width: 10px;
		height: 10px;
		border-radius: 50%;
	}

	.status-indicator.checking {
		background: #f59e0b;
		animation: pulse 1s infinite;
	}

	.status-indicator.supported {
		background: #4ade80;
	}

	.status-indicator.unsupported {
		background: #f87171;
	}

	@keyframes pulse {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.5;
		}
	}

	.container {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.model-section {
		background: #1a1a1a;
		padding: 1.5rem;
		border-radius: 12px;
	}

	.model-section h3 {
		margin: 0 0 1rem 0;
		font-size: 1rem;
		color: #888;
	}

	.model-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
		gap: 0.75rem;
		margin-bottom: 1rem;
	}

	.model-option {
		padding: 0.75rem;
		background: #2a2a2a;
		border: 1px solid #333;
		border-radius: 8px;
		cursor: pointer;
		text-align: left;
		transition: all 0.2s;
	}

	.model-option:hover {
		background: #333;
	}

	.model-option.active {
		background: rgba(250, 112, 154, 0.2);
		border-color: #fa709a;
	}

	.model-name {
		display: block;
		font-weight: 600;
		color: #fafafa;
	}

	.model-meta {
		display: block;
		font-size: 0.75rem;
		color: #888;
		margin-top: 0.25rem;
	}

	.load-btn {
		padding: 0.75rem 2rem;
		background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
		color: white;
		border: none;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 600;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.load-btn:disabled {
		opacity: 0.7;
		cursor: not-allowed;
	}

	.spinner {
		width: 16px;
		height: 16px;
		border: 2px solid white;
		border-top-color: transparent;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.model-ready {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		color: #4ade80;
		font-weight: 500;
	}

	.check {
		font-size: 1.25rem;
	}

	.input-section {
		background: #1a1a1a;
		padding: 1.5rem;
		border-radius: 12px;
	}

	.input-section h3 {
		margin: 0 0 1rem 0;
		font-size: 1rem;
		color: #888;
	}

	.input-buttons {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.input-btn {
		padding: 0.75rem 1.5rem;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 500;
		border: none;
		transition: opacity 0.2s;
	}

	.input-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.input-btn.webcam {
		background: #4facfe;
		color: white;
	}

	.input-btn.file {
		background: #2a2a2a;
		color: #fafafa;
		border: 1px solid #333;
	}

	.input-btn.file input {
		display: none;
	}

	.input-btn.stop {
		background: #f87171;
		color: white;
	}

	.settings-section {
		background: #1a1a1a;
		padding: 1rem 1.5rem;
		border-radius: 12px;
		display: flex;
		gap: 2rem;
		flex-wrap: wrap;
		align-items: center;
	}

	.setting label {
		color: #888;
		font-size: 0.875rem;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.setting input[type='range'] {
		width: 100px;
	}

	.setting input[type='checkbox'] {
		accent-color: #fa709a;
	}

	.video-section {
		background: #1a1a1a;
		padding: 1rem;
		border-radius: 12px;
	}

	.video-container {
		position: relative;
		background: #0a0a0a;
		border-radius: 8px;
		overflow: hidden;
		aspect-ratio: 4/3;
	}

	.video-element {
		width: 100%;
		height: 100%;
		object-fit: contain;
	}

	.detection-overlay {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}

	.video-placeholder {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		text-align: center;
		color: #666;
	}

	.stats-bar {
		display: flex;
		gap: 2rem;
		padding: 1rem;
		background: #0a0a0a;
		border-radius: 8px;
		margin-top: 1rem;
	}

	.stat {
		display: flex;
		flex-direction: column;
	}

	.stat-label {
		font-size: 0.75rem;
		color: #666;
		text-transform: uppercase;
	}

	.stat-value {
		font-size: 1.5rem;
		font-weight: 700;
		color: #fa709a;
	}

	.detection-list {
		margin-top: 1rem;
	}

	.detection-list h4 {
		margin: 0 0 0.75rem 0;
		font-size: 0.875rem;
		color: #888;
	}

	.detection-chips {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.detection-chip {
		background: #2a2a2a;
		padding: 0.5rem 0.75rem;
		border-radius: 6px;
		font-size: 0.875rem;
	}

	.detection-chip small {
		color: #888;
		margin-left: 0.25rem;
	}

	.info-section {
		background: #1a1a1a;
		padding: 1.5rem;
		border-radius: 12px;
	}

	.info-section h2 {
		margin: 0 0 1rem 0;
		font-size: 1.25rem;
	}

	.info-section h3 {
		margin: 1.5rem 0 0.75rem 0;
		font-size: 1rem;
		color: #888;
	}

	.info-content p {
		color: #aaa;
		line-height: 1.6;
		margin: 0 0 1rem 0;
	}

	.info-content ul {
		margin: 0;
		padding-left: 1.5rem;
	}

	.info-content li {
		color: #888;
		margin: 0.5rem 0;
	}

	.code-block {
		background: #0a0a0a;
		padding: 1rem;
		border-radius: 8px;
		overflow-x: auto;
	}

	.code-block code {
		color: #4ade80;
		font-size: 0.875rem;
		line-height: 1.6;
	}
</style>
