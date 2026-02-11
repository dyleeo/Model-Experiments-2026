import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));

/** @type {import('./$types').RequestHandler} */
export async function GET({ params }) {
	const model = params.model;
	if (!model || !/^yolov8[nslm]$/.test(model)) {
		return new Response('Invalid model', { status: 400 });
	}
	try {
		// Resolve static folder: from src/routes/api/yolo-model/[model] go up 5 levels to project root
		const projectRoot = join(__dirname, '../../../../..');
		const filePath = join(projectRoot, 'static', 'models', `${model}.onnx`);
		const buf = await readFile(filePath);
		return new Response(buf, {
			headers: {
				'Content-Type': 'application/octet-stream',
				'Cache-Control': 'public, max-age=3600'
			}
		});
	} catch (e) {
		console.warn('YOLO model serve error:', e?.message);
		return new Response('Model not found', { status: 404 });
	}
}
