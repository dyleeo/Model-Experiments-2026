<script>
	import { onMount } from 'svelte';

	// Model state
	let modelLoaded = $state(false);
	let isLoadingModel = $state(false);
	let webgpuSupported = $state(null);

	// Image state
	let imageFile = $state(null);
	let imagePreview = $state(null);
	let imageElement = $state(null);

	// Segmentation state
	let allMasks = $state([]);
	let selectedMask = $state(null);
	let isSegmenting = $state(false);

	// Prompt state
	let promptMode = $state('everything'); // 'everything', 'point', 'box', 'text'
	let points = $state([]);
	let textPrompt = $state('');

	// Canvas refs
	let overlayRef = $state(null);

	onMount(async () => {
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
		try {
			// Simulated model loading
			await new Promise((resolve) => setTimeout(resolve, 1800));
			modelLoaded = true;
		} catch (e) {
			console.error('Model load error:', e);
		} finally {
			isLoadingModel = false;
		}
	}

	function handleImageSelect(event) {
		const file = event.target.files?.[0];
		if (!file) return;

		imageFile = file;
		imagePreview = URL.createObjectURL(file);
		allMasks = [];
		selectedMask = null;
		points = [];
	}

	function handleImageLoad(event) {
		imageElement = event.target;
		if (overlayRef) {
			overlayRef.width = imageElement.clientWidth;
			overlayRef.height = imageElement.clientHeight;
		}
	}

	async function runSegmentation() {
		if (!modelLoaded || !imageElement) return;

		isSegmenting = true;
		allMasks = [];

		try {
			// Simulated inference
			await new Promise((resolve) => setTimeout(resolve, 800));

			// Generate mock masks based on mode
			if (promptMode === 'everything') {
				allMasks = generateMockMasks(8);
			} else if (promptMode === 'point' && points.length > 0) {
				allMasks = generateMockMasks(1);
			} else if (promptMode === 'text' && textPrompt) {
				allMasks = generateMockMasks(2);
			}

			if (allMasks.length > 0) {
				selectedMask = 0;
			}

			drawMasks();
		} catch (e) {
			console.error('Segmentation error:', e);
		} finally {
			isSegmenting = false;
		}
	}

	function generateMockMasks(count) {
		const masks = [];
		const colors = ['#4facfe', '#f093fb', '#4ade80', '#f59e0b', '#f87171', '#a78bfa', '#34d399', '#fbbf24'];

		for (let i = 0; i < count; i++) {
			masks.push({
				id: i,
				area: Math.random() * 50000 + 5000,
				score: 0.7 + Math.random() * 0.25,
				color: colors[i % colors.length],
				bbox: {
					x: Math.random() * 300 + 50,
					y: Math.random() * 200 + 50,
					width: 80 + Math.random() * 150,
					height: 80 + Math.random() * 150
				}
			});
		}

		return masks.sort((a, b) => b.area - a.area);
	}

	function handleCanvasClick(event) {
		if (promptMode !== 'point' || !imageElement) return;

		const rect = event.target.getBoundingClientRect();
		const x = ((event.clientX - rect.left) / rect.width) * imageElement.naturalWidth;
		const y = ((event.clientY - rect.top) / rect.height) * imageElement.naturalHeight;

		points = [...points, { x, y }];
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
			ctx.fillStyle = '#4ade80';
			ctx.fill();
			ctx.strokeStyle = 'white';
			ctx.lineWidth = 2;
			ctx.stroke();
		});
	}

	function drawMasks() {
		if (!overlayRef || !imageElement) return;

		const ctx = overlayRef.getContext('2d');
		const scaleX = overlayRef.width / imageElement.naturalWidth;
		const scaleY = overlayRef.height / imageElement.naturalHeight;

		ctx.clearRect(0, 0, overlayRef.width, overlayRef.height);

		// Draw all masks or just selected
		const masksToDraw = selectedMask !== null ? [allMasks[selectedMask]] : allMasks;

		masksToDraw.forEach((mask) => {
			ctx.fillStyle = mask.color + '60';
			ctx.fillRect(
				mask.bbox.x * scaleX,
				mask.bbox.y * scaleY,
				mask.bbox.width * scaleX,
				mask.bbox.height * scaleY
			);

			ctx.strokeStyle = mask.color;
			ctx.lineWidth = 2;
			ctx.strokeRect(
				mask.bbox.x * scaleX,
				mask.bbox.y * scaleY,
				mask.bbox.width * scaleX,
				mask.bbox.height * scaleY
			);
		});
	}

	function clearAll() {
		points = [];
		allMasks = [];
		selectedMask = null;
		textPrompt = '';
		if (overlayRef) {
			const ctx = overlayRef.getContext('2d');
			ctx.clearRect(0, 0, overlayRef.width, overlayRef.height);
		}
	}

	let imageLoaded = $derived(!!imageElement);
</script>

<svelte:head>
	<title>FastSAM - Model Experiments 2026</title>
</svelte:head>

<main>
	<nav class="breadcrumb">
		<a href="/">← Back to experiments</a>
	</nav>

	<h1>FastSAM</h1>
	<p class="subtitle">Fast Segment Anything - CNN-based real-time segmentation</p>

	<div class="badge-row">
		<span class="badge browser">Browser</span>
		<span class="badge">WebGPU</span>
		<span class="badge">YOLOv8-seg</span>
		<span class="badge">10-100× Faster</span>
	</div>

	<!-- WebGPU Status -->
	<div class="status-card">
		{#if webgpuSupported === null}
			<span class="status-indicator checking"></span>
			Checking WebGPU support...
		{:else if webgpuSupported}
			<span class="status-indicator supported"></span>
			WebGPU supported
		{:else}
			<span class="status-indicator unsupported"></span>
			WebGPU not supported - will use WASM fallback
		{/if}
	</div>

	<div class="container">
		<!-- Model Loading -->
		<section class="model-section">
			{#if !modelLoaded}
				<div class="model-card">
					<h3>Load FastSAM Model</h3>
					<p>YOLOv8-seg based model for fast all-instance segmentation (~25MB)</p>
					<button class="load-btn" onclick={loadModel} disabled={isLoadingModel}>
						{#if isLoadingModel}
							<span class="spinner"></span>
							Loading...
						{:else}
							Load Model
						{/if}
					</button>
				</div>
			{:else}
				<div class="model-ready">
					<span class="check">✓</span>
					FastSAM loaded
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

			{#if imageLoaded}
				<!-- Mode Selection -->
				<section class="mode-section">
					<h3>Segmentation Mode</h3>
					<div class="mode-grid">
						<button
							class="mode-card"
							class:active={promptMode === 'everything'}
							onclick={() => {
								promptMode = 'everything';
								clearAll();
							}}
						>
							<span class="mode-icon">🎯</span>
							<span class="mode-name">Everything</span>
							<span class="mode-desc">Segment all objects</span>
						</button>
						<button
							class="mode-card"
							class:active={promptMode === 'point'}
							onclick={() => {
								promptMode = 'point';
								clearAll();
							}}
						>
							<span class="mode-icon">👆</span>
							<span class="mode-name">Point</span>
							<span class="mode-desc">Click to select</span>
						</button>
						<button
							class="mode-card"
							class:active={promptMode === 'text'}
							onclick={() => {
								promptMode = 'text';
								clearAll();
							}}
						>
							<span class="mode-icon">💬</span>
							<span class="mode-name">Text</span>
							<span class="mode-desc">Describe object</span>
						</button>
					</div>
				</section>

				<!-- Text Prompt (if in text mode) -->
				{#if promptMode === 'text'}
					<section class="text-prompt-section">
						<input
							type="text"
							bind:value={textPrompt}
							placeholder="Describe what to segment (e.g., 'person', 'dog')"
							class="text-input"
						/>
					</section>
				{/if}

				<!-- Action Button -->
				<section class="action-section">
					<button
						class="segment-btn"
						onclick={runSegmentation}
						disabled={isSegmenting || (promptMode === 'point' && points.length === 0) || (promptMode === 'text' && !textPrompt)}
					>
						{isSegmenting ? 'Segmenting...' : 'Run Segmentation'}
					</button>
					<button class="clear-btn" onclick={clearAll}>Clear</button>
				</section>

				<!-- Canvas Section -->
				<section class="canvas-section">
					<div class="canvas-container" onclick={handleCanvasClick} role="button" tabindex="0">
						<img src={imagePreview} alt="Input" class="input-image" onload={handleImageLoad} />
						<canvas bind:this={overlayRef} class="overlay-canvas"></canvas>
					</div>

					{#if promptMode === 'point'}
						<p class="hint">Click on the image to add points. {points.length} point(s) selected.</p>
					{/if}
				</section>

				<!-- Results -->
				{#if allMasks.length > 0}
					<section class="results-section">
						<h3>Segmentation Results ({allMasks.length} masks)</h3>
						<div class="mask-grid">
							{#each allMasks as mask, i}
								<button
									class="mask-card"
									class:selected={selectedMask === i}
									onclick={() => {
										selectedMask = selectedMask === i ? null : i;
										drawMasks();
									}}
								>
									<div class="mask-color" style="background: {mask.color}"></div>
									<div class="mask-info">
										<span class="mask-id">Mask {i + 1}</span>
										<span class="mask-score">{(mask.score * 100).toFixed(0)}%</span>
									</div>
								</button>
							{/each}
						</div>
						<p class="hint">Click a mask to isolate it, or click again to show all.</p>
					</section>
				{/if}
			{/if}
		{/if}

		<!-- About Section -->
		<section class="about-section">
			<h2>About FastSAM</h2>
			<div class="about-content">
				<p>
					FastSAM is a CNN-based solution to the Segment Anything task. It reformulates the task as
					all-instance segmentation using a YOLOv8-seg model, achieving 50× faster performance than SAM
					while maintaining competitive accuracy.
				</p>

				<div class="comparison">
					<h3>FastSAM vs SAM</h3>
					<table>
						<thead>
							<tr>
								<th>Aspect</th>
								<th>SAM</th>
								<th>FastSAM</th>
							</tr>
						</thead>
						<tbody>
							<tr>
								<td>Architecture</td>
								<td>ViT-H (Transformer)</td>
								<td>YOLOv8-seg (CNN)</td>
							</tr>
							<tr>
								<td>Speed</td>
								<td>~500ms</td>
								<td>~10-50ms</td>
							</tr>
							<tr>
								<td>Model Size</td>
								<td>2.4GB</td>
								<td>~140MB</td>
							</tr>
							<tr>
								<td>Browser Support</td>
								<td>Difficult</td>
								<td>Good</td>
							</tr>
						</tbody>
					</table>
				</div>

				<h3>How It Works</h3>
				<ol>
					<li><strong>All-instance segmentation:</strong> YOLOv8-seg generates masks for all objects</li>
					<li><strong>Prompt-guided selection:</strong> Masks are filtered based on user prompts</li>
					<li><strong>Post-processing:</strong> Morphological operations refine mask boundaries</li>
				</ol>
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
		color: #a8edea;
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
		background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
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
		background: rgba(168, 237, 234, 0.2);
		color: #a8edea;
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
		background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
		color: #1a1a1a;
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
		border: 2px solid #1a1a1a;
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

	.upload-section {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.upload-btn {
		padding: 0.75rem 1.5rem;
		background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
		color: #1a1a1a;
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
		background: #1a1a1a;
		padding: 1.5rem;
		border-radius: 12px;
	}

	.mode-section h3 {
		margin: 0 0 1rem 0;
		font-size: 1rem;
		color: #888;
	}

	.mode-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.75rem;
	}

	.mode-card {
		padding: 1rem;
		background: #2a2a2a;
		border: 1px solid #333;
		border-radius: 8px;
		cursor: pointer;
		text-align: center;
		transition: all 0.2s;
	}

	.mode-card:hover {
		background: #333;
	}

	.mode-card.active {
		background: rgba(168, 237, 234, 0.1);
		border-color: #a8edea;
	}

	.mode-icon {
		display: block;
		font-size: 1.5rem;
		margin-bottom: 0.5rem;
	}

	.mode-name {
		display: block;
		font-weight: 600;
		color: #fafafa;
	}

	.mode-desc {
		display: block;
		font-size: 0.75rem;
		color: #888;
		margin-top: 0.25rem;
	}

	.text-prompt-section {
		background: #1a1a1a;
		padding: 1rem;
		border-radius: 12px;
	}

	.text-input {
		width: 100%;
		padding: 0.75rem 1rem;
		background: #0a0a0a;
		border: 1px solid #333;
		border-radius: 8px;
		color: #fafafa;
		font-size: 1rem;
	}

	.text-input:focus {
		outline: none;
		border-color: #a8edea;
	}

	.action-section {
		display: flex;
		gap: 0.75rem;
	}

	.segment-btn {
		padding: 0.75rem 2rem;
		background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
		color: #1a1a1a;
		border: none;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 600;
	}

	.segment-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.clear-btn {
		padding: 0.75rem 1.5rem;
		background: #2a2a2a;
		color: #fafafa;
		border: 1px solid #333;
		border-radius: 8px;
		cursor: pointer;
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

	.overlay-canvas {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		border-radius: 8px;
	}

	.hint {
		margin: 0.75rem 0 0 0;
		color: #888;
		font-size: 0.875rem;
	}

	.results-section {
		background: #1a1a1a;
		padding: 1.5rem;
		border-radius: 12px;
	}

	.results-section h3 {
		margin: 0 0 1rem 0;
		font-size: 1rem;
	}

	.mask-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
		gap: 0.5rem;
	}

	.mask-card {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem;
		background: #2a2a2a;
		border: 1px solid #333;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.2s;
	}

	.mask-card:hover {
		background: #333;
	}

	.mask-card.selected {
		border-color: #4ade80;
		background: rgba(74, 222, 128, 0.1);
	}

	.mask-color {
		width: 16px;
		height: 16px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.mask-info {
		display: flex;
		flex-direction: column;
	}

	.mask-id {
		font-size: 0.875rem;
		font-weight: 500;
	}

	.mask-score {
		font-size: 0.75rem;
		color: #888;
	}

	.about-section {
		background: #1a1a1a;
		padding: 1.5rem;
		border-radius: 12px;
	}

	.about-section h2 {
		margin: 0 0 1rem 0;
	}

	.about-section h3 {
		margin: 1.5rem 0 0.75rem 0;
		font-size: 1rem;
		color: #888;
	}

	.about-content p {
		color: #aaa;
		line-height: 1.6;
		margin: 0 0 1rem 0;
	}

	.about-content ol {
		padding-left: 1.5rem;
		color: #aaa;
	}

	.about-content li {
		margin: 0.5rem 0;
	}

	.comparison {
		margin-top: 1.5rem;
	}

	.comparison table {
		width: 100%;
		border-collapse: collapse;
		background: #0a0a0a;
		border-radius: 8px;
		overflow: hidden;
	}

	.comparison th,
	.comparison td {
		padding: 0.75rem 1rem;
		text-align: left;
		border-bottom: 1px solid #2a2a2a;
	}

	.comparison th {
		background: #1a1a1a;
		color: #888;
		font-weight: 600;
		font-size: 0.875rem;
	}

	.comparison tr:last-child td {
		border-bottom: none;
	}

	.comparison td {
		color: #ccc;
	}

	.comparison td:first-child {
		color: #fafafa;
		font-weight: 500;
	}
</style>
