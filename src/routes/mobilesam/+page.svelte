<script>
	import { onMount } from 'svelte';

	// Model state
	let modelLoaded = $state(false);
	let isLoadingModel = $state(false);
	let modelError = $state(null);
	let webgpuSupported = $state(null);

	// Image state
	let imageFile = $state(null);
	let imagePreview = $state(null);
	let imageElement = $state(null);

	// Interaction state
	let points = $state([]);
	let boxes = $state([]);
	let isDrawingBox = $state(false);
	let boxStart = $state(null);
	let currentBox = $state(null);

	// Segmentation state
	let masks = $state([]);
	let isSegmenting = $state(false);
	let promptMode = $state('point'); // 'point' or 'box'

	// Canvas refs
	let canvasRef = $state(null);
	let overlayRef = $state(null);

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
			// In a real implementation, this would load the ONNX model
			// For demo purposes, we'll simulate the loading
			await new Promise((resolve) => setTimeout(resolve, 2000));

			// Simulated model loading
			// const ort = await import('onnxruntime-web/webgpu');
			// session = await ort.InferenceSession.create('/models/mobilesam.onnx', {
			//   executionProviders: ['webgpu', 'wasm']
			// });

			modelLoaded = true;
		} catch (e) {
			modelError = e.message;
		} finally {
			isLoadingModel = false;
		}
	}

	function handleImageSelect(event) {
		const file = event.target.files?.[0];
		if (!file) return;

		imageFile = file;
		imagePreview = URL.createObjectURL(file);
		points = [];
		boxes = [];
		masks = [];
	}

	function handleCanvasClick(event) {
		if (!imageLoaded || promptMode !== 'point') return;

		const rect = canvasRef.getBoundingClientRect();
		const x = ((event.clientX - rect.left) / rect.width) * imageElement.naturalWidth;
		const y = ((event.clientY - rect.top) / rect.height) * imageElement.naturalHeight;

		// Toggle between positive (1) and negative (0) points with right-click
		const label = event.button === 2 ? 0 : 1;

		points = [...points, { x, y, label }];
		drawOverlay();
	}

	function handleMouseDown(event) {
		if (!imageLoaded || promptMode !== 'box') return;

		const rect = canvasRef.getBoundingClientRect();
		const x = ((event.clientX - rect.left) / rect.width) * imageElement.naturalWidth;
		const y = ((event.clientY - rect.top) / rect.height) * imageElement.naturalHeight;

		isDrawingBox = true;
		boxStart = { x, y };
	}

	function handleMouseMove(event) {
		if (!isDrawingBox || !boxStart) return;

		const rect = canvasRef.getBoundingClientRect();
		const x = ((event.clientX - rect.left) / rect.width) * imageElement.naturalWidth;
		const y = ((event.clientY - rect.top) / rect.height) * imageElement.naturalHeight;

		currentBox = {
			x1: Math.min(boxStart.x, x),
			y1: Math.min(boxStart.y, y),
			x2: Math.max(boxStart.x, x),
			y2: Math.max(boxStart.y, y)
		};

		drawOverlay();
	}

	function handleMouseUp() {
		if (isDrawingBox && currentBox) {
			boxes = [currentBox]; // Single box for now
		}
		isDrawingBox = false;
		boxStart = null;
		currentBox = null;
		drawOverlay();
	}

	function drawOverlay() {
		if (!overlayRef || !imageElement) return;

		const ctx = overlayRef.getContext('2d');
		const scaleX = overlayRef.width / imageElement.naturalWidth;
		const scaleY = overlayRef.height / imageElement.naturalHeight;

		ctx.clearRect(0, 0, overlayRef.width, overlayRef.height);

		// Draw points
		points.forEach((point) => {
			ctx.beginPath();
			ctx.arc(point.x * scaleX, point.y * scaleY, 8, 0, Math.PI * 2);
			ctx.fillStyle = point.label === 1 ? '#4ade80' : '#f87171';
			ctx.fill();
			ctx.strokeStyle = 'white';
			ctx.lineWidth = 2;
			ctx.stroke();
		});

		// Draw boxes
		[...boxes, currentBox].filter(Boolean).forEach((box) => {
			ctx.strokeStyle = '#4facfe';
			ctx.lineWidth = 2;
			ctx.strokeRect(
				box.x1 * scaleX,
				box.y1 * scaleY,
				(box.x2 - box.x1) * scaleX,
				(box.y2 - box.y1) * scaleY
			);
		});
	}

	async function runSegmentation() {
		if (!modelLoaded || (!points.length && !boxes.length)) return;

		isSegmenting = true;

		try {
			// In a real implementation, this would run inference
			await new Promise((resolve) => setTimeout(resolve, 500));

			// Simulated mask result
			masks = [{ id: 1, score: 0.95 }];
		} catch (e) {
			console.error('Segmentation error:', e);
		} finally {
			isSegmenting = false;
		}
	}

	function clearPrompts() {
		points = [];
		boxes = [];
		masks = [];
		if (overlayRef) {
			const ctx = overlayRef.getContext('2d');
			ctx.clearRect(0, 0, overlayRef.width, overlayRef.height);
		}
	}

	function handleImageLoad(event) {
		imageElement = event.target;
		if (canvasRef) {
			canvasRef.width = imageElement.naturalWidth;
			canvasRef.height = imageElement.naturalHeight;
		}
		if (overlayRef) {
			overlayRef.width = imageElement.clientWidth;
			overlayRef.height = imageElement.clientHeight;
		}
	}

	let imageLoaded = $derived(!!imageElement);
</script>

<svelte:head>
	<title>MobileSAM - Model Experiments 2026</title>
</svelte:head>

<main>
	<nav class="breadcrumb">
		<a href="/">← Back to experiments</a>
	</nav>

	<h1>MobileSAM</h1>
	<p class="subtitle">Lightweight segmentation in browser - WebGPU accelerated</p>

	<div class="badge-row">
		<span class="badge browser">Browser</span>
		<span class="badge">WebGPU</span>
		<span class="badge">9.66M params</span>
		<span class="badge">ONNX Runtime</span>
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
			WebGPU not supported - will use WASM fallback (slower)
		{/if}
	</div>

	<div class="container">
		<!-- Model Loading -->
		<section class="model-section">
			{#if !modelLoaded}
				<div class="model-card">
					<h3>Load MobileSAM Model</h3>
					<p>Download and initialize the model (~10MB). Runs entirely in your browser.</p>
					<button onclick={loadModel} disabled={isLoadingModel} class="load-btn">
						{#if isLoadingModel}
							<span class="spinner"></span>
							Loading model...
						{:else}
							Load Model
						{/if}
					</button>
					{#if modelError}
						<p class="error-text">{modelError}</p>
					{/if}
				</div>
			{:else}
				<div class="model-ready">
					<span class="check">✓</span>
					Model loaded and ready
				</div>
			{/if}
		</section>

		{#if modelLoaded}
			<!-- Upload Section -->
			<section class="upload-section">
				<label class="upload-btn">
					<input type="file" accept="image/*" onchange={handleImageSelect} />
					{imageFile ? 'Change Image' : 'Upload Image'}
				</label>

				{#if imageFile}
					<span class="filename">{imageFile.name}</span>
				{/if}
			</section>

			<!-- Prompt Mode Selection -->
			{#if imageLoaded}
				<section class="mode-section">
					<span class="mode-label">Prompt Mode:</span>
					<button class="mode-btn" class:active={promptMode === 'point'} onclick={() => (promptMode = 'point')}>
						Point Prompt
					</button>
					<button class="mode-btn" class:active={promptMode === 'box'} onclick={() => (promptMode = 'box')}>
						Box Prompt
					</button>
					<button class="clear-btn" onclick={clearPrompts}>Clear</button>
				</section>

				<div class="instructions-inline">
					{#if promptMode === 'point'}
						<p>Click to add positive points (green). Right-click for negative points (red).</p>
					{:else}
						<p>Click and drag to draw a bounding box around the object.</p>
					{/if}
				</div>
			{/if}

			<!-- Canvas Section -->
			{#if imagePreview}
				<section class="canvas-section">
					<div
						class="canvas-container"
						onmousedown={promptMode === 'box' ? handleMouseDown : null}
						onmousemove={handleMouseMove}
						onmouseup={handleMouseUp}
						onmouseleave={handleMouseUp}
						onclick={promptMode === 'point' ? handleCanvasClick : null}
						oncontextmenu={(e) => {
							e.preventDefault();
							if (promptMode === 'point') handleCanvasClick(e);
						}}
						role="button"
						tabindex="0"
					>
						<img src={imagePreview} alt="Input" class="input-image" onload={handleImageLoad} />
						<canvas bind:this={canvasRef} class="hidden-canvas"></canvas>
						<canvas bind:this={overlayRef} class="overlay-canvas"></canvas>
					</div>

					<!-- Prompt Summary -->
					{#if points.length > 0 || boxes.length > 0}
						<div class="prompt-summary">
							{#if points.length > 0}
								<span>{points.filter((p) => p.label === 1).length} positive, {points.filter((p) => p.label === 0).length} negative points</span>
							{/if}
							{#if boxes.length > 0}
								<span>1 bounding box</span>
							{/if}
							<button class="segment-btn" onclick={runSegmentation} disabled={isSegmenting}>
								{isSegmenting ? 'Segmenting...' : 'Run Segmentation'}
							</button>
						</div>
					{/if}

					<!-- Results -->
					{#if masks.length > 0}
						<div class="results">
							<h4>Segmentation Result</h4>
							<p>Found {masks.length} mask(s) - Score: {(masks[0].score * 100).toFixed(1)}%</p>
							<p class="demo-note">
								Note: This is a demo UI. In production, the actual mask would overlay the image.
							</p>
						</div>
					{/if}
				</section>
			{/if}
		{/if}

		<!-- Info Section -->
		<section class="info-section">
			<h2>About MobileSAM</h2>
			<div class="info-content">
				<p>
					MobileSAM is a lightweight variant of SAM designed for mobile and edge devices. It replaces
					SAM's heavy ViT encoder (632M params) with TinyViT (5.78M params), achieving:
				</p>
				<ul>
					<li><strong>66× smaller</strong> than original SAM</li>
					<li><strong>5-38× faster</strong> inference</li>
					<li>Full compatibility with SAM's prompting interface</li>
					<li>Runs entirely in browser via ONNX Runtime + WebGPU</li>
				</ul>
			</div>

			<h3>Implementation Notes</h3>
			<div class="code-block">
				<code>
					// To implement, install onnxruntime-web<br />
					npm install onnxruntime-web<br /><br />
					// Load model with WebGPU backend<br />
					import * as ort from 'onnxruntime-web/webgpu';<br />
					const session = await ort.InferenceSession.create(<br />
					&nbsp;&nbsp;'/models/mobilesam.onnx',<br />
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
		color: #4facfe;
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
		background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
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
		background: rgba(79, 172, 254, 0.2);
		color: #4facfe;
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

	.model-card h3 {
		margin: 0 0 0.5rem 0;
	}

	.model-card p {
		color: #888;
		margin: 0 0 1rem 0;
	}

	.load-btn {
		padding: 0.75rem 2rem;
		background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
		color: white;
		border: none;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 600;
		font-size: 1rem;
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

	.error-text {
		color: #f87171;
		margin-top: 0.5rem;
	}

	.upload-section {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.upload-btn {
		padding: 0.75rem 1.5rem;
		background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
		color: white;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 500;
	}

	.upload-btn input {
		display: none;
	}

	.filename {
		color: #888;
		font-size: 0.875rem;
	}

	.mode-section {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.mode-label {
		color: #888;
		font-size: 0.875rem;
	}

	.mode-btn {
		padding: 0.5rem 1rem;
		background: #2a2a2a;
		color: #fafafa;
		border: 1px solid #333;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.875rem;
		transition: all 0.2s;
	}

	.mode-btn:hover {
		background: #333;
	}

	.mode-btn.active {
		background: #4facfe;
		border-color: #4facfe;
	}

	.clear-btn {
		padding: 0.5rem 1rem;
		background: transparent;
		color: #888;
		border: 1px solid #333;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.875rem;
		margin-left: auto;
	}

	.clear-btn:hover {
		background: #2a2a2a;
		color: #fafafa;
	}

	.instructions-inline {
		background: #1a1a1a;
		padding: 0.75rem 1rem;
		border-radius: 8px;
	}

	.instructions-inline p {
		margin: 0;
		color: #888;
		font-size: 0.875rem;
	}

	.canvas-section {
		background: #1a1a1a;
		padding: 1rem;
		border-radius: 12px;
	}

	.canvas-container {
		position: relative;
		display: inline-block;
		max-width: 100%;
		cursor: crosshair;
	}

	.input-image {
		max-width: 100%;
		max-height: 500px;
		border-radius: 8px;
		display: block;
	}

	.hidden-canvas {
		display: none;
	}

	.overlay-canvas {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		border-radius: 8px;
	}

	.prompt-summary {
		margin-top: 1rem;
		padding: 1rem;
		background: #0a0a0a;
		border-radius: 8px;
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.prompt-summary span {
		color: #888;
		font-size: 0.875rem;
	}

	.segment-btn {
		padding: 0.5rem 1.5rem;
		background: #4facfe;
		color: white;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-weight: 500;
		margin-left: auto;
	}

	.segment-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.results {
		margin-top: 1rem;
		padding: 1rem;
		background: rgba(74, 222, 128, 0.1);
		border: 1px solid rgba(74, 222, 128, 0.3);
		border-radius: 8px;
	}

	.results h4 {
		margin: 0 0 0.5rem 0;
		color: #4ade80;
	}

	.results p {
		margin: 0;
		color: #888;
	}

	.demo-note {
		margin-top: 0.5rem !important;
		font-style: italic;
		font-size: 0.875rem;
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
