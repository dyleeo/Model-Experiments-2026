<script>
	// Media state
	let mediaType = $state('none'); // 'none', 'image', 'video'
	let imageFile = $state(null);
	let imagePreview = $state(null);

	// Video state
	let videoMetadata = $state(null);
	let currentFrameIndex = $state(0);
	let currentFrameImage = $state(null);
	let thumbnails = $state([]);

	// Segmentation state
	let textPrompt = $state('');
	let masks = $state([]);
	let isLoading = $state(false);
	let error = $state(null);
	let imageLoaded = $state(false);
	let selectedMaskIndex = $state(0);

	const API_URL = 'http://localhost:8000';

	// ============== Image Handling ==============

	async function handleImageSelect(event) {
		const file = event.target.files?.[0];
		if (!file) return;

		resetState();
		mediaType = 'image';
		imageFile = file;
		imagePreview = URL.createObjectURL(file);

		isLoading = true;
		try {
			const formData = new FormData();
			formData.append('file', file);

			const response = await fetch(`${API_URL}/api/set-image`, {
				method: 'POST',
				body: formData
			});

			if (!response.ok) {
				throw new Error('Failed to upload image');
			}

			const data = await response.json();
			console.log('Image uploaded:', data);
			imageLoaded = true;
		} catch (e) {
			error = e.message;
			console.error('Upload error:', e);
		} finally {
			isLoading = false;
		}
	}

	// ============== Video Handling ==============

	async function handleVideoSelect(event) {
		const file = event.target.files?.[0];
		if (!file) return;

		resetState();
		mediaType = 'video';
		isLoading = true;
		error = null;

		try {
			const formData = new FormData();
			formData.append('file', file);

			const response = await fetch(`${API_URL}/api/video/upload`, {
				method: 'POST',
				body: formData
			});

			if (!response.ok) {
				const errData = await response.json();
				throw new Error(errData.detail || 'Failed to upload video');
			}

			videoMetadata = await response.json();
			console.log('Video uploaded:', videoMetadata);

			// Load thumbnails
			await loadThumbnails();

			// Load first frame
			await setFrame(0);
		} catch (e) {
			error = e.message;
			console.error('Video upload error:', e);
			mediaType = 'none';
		} finally {
			isLoading = false;
		}
	}

	async function loadThumbnails() {
		try {
			const response = await fetch(`${API_URL}/api/video/thumbnails?count=12`);
			if (response.ok) {
				const data = await response.json();
				thumbnails = data.thumbnails || [];
			}
		} catch (e) {
			console.error('Failed to load thumbnails:', e);
		}
	}

	async function setFrame(frameIndex) {
		if (!videoMetadata) return;

		isLoading = true;
		masks = [];
		error = null;

		try {
			// Get frame image for display
			const frameResponse = await fetch(`${API_URL}/api/video/frame/${frameIndex}`);
			if (!frameResponse.ok) throw new Error('Failed to get frame');

			const frameData = await frameResponse.json();
			currentFrameImage = `data:image/jpeg;base64,${frameData.frame}`;
			currentFrameIndex = frameIndex;

			// Set frame for segmentation
			const setResponse = await fetch(`${API_URL}/api/video/set-frame`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ frame_index: frameIndex })
			});

			if (!setResponse.ok) throw new Error('Failed to set frame for segmentation');

			imageLoaded = true;
		} catch (e) {
			error = e.message;
			console.error('Frame error:', e);
		} finally {
			isLoading = false;
		}
	}

	function handleFrameSlider(event) {
		const frameIndex = parseInt(event.target.value);
		setFrame(frameIndex);
	}

	// ============== Segmentation ==============

	async function segmentWithText() {
		if (!textPrompt.trim() || !imageLoaded) return;

		isLoading = true;
		error = null;
		masks = [];

		try {
			const response = await fetch(`${API_URL}/api/segment/text`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ prompt: textPrompt })
			});

			if (!response.ok) {
				const errData = await response.json();
				throw new Error(errData.detail || 'Segmentation failed');
			}

			const data = await response.json();
			masks = data.masks || [];
			selectedMaskIndex = 0;
			console.log(`Found ${masks.length} objects`);
		} catch (e) {
			error = e.message;
			console.error('Segmentation error:', e);
		} finally {
			isLoading = false;
		}
	}

	function handleKeydown(event) {
		if (event.key === 'Enter') {
			segmentWithText();
		}
	}

	// ============== Utilities ==============

	function resetState() {
		mediaType = 'none';
		imageFile = null;
		imagePreview = null;
		videoMetadata = null;
		currentFrameIndex = 0;
		currentFrameImage = null;
		thumbnails = [];
		masks = [];
		error = null;
		imageLoaded = false;
		selectedMaskIndex = 0;
		textPrompt = '';
	}

	function formatDuration(seconds) {
		const mins = Math.floor(seconds / 60);
		const secs = Math.floor(seconds % 60);
		return `${mins}:${secs.toString().padStart(2, '0')}`;
	}

	// Current display image (either uploaded image or video frame)
	let displayImage = $derived(mediaType === 'video' ? currentFrameImage : imagePreview);
</script>

<svelte:head>
	<title>SAM 3 - Model Experiments 2026</title>
</svelte:head>

<main>
	<nav class="breadcrumb">
		<a href="/">← Back to experiments</a>
	</nav>

	<h1>SAM 3 Segmentation</h1>
	<p class="subtitle">Segment anything with text prompts - server-side inference</p>

	<div class="badge-row">
		<span class="badge server">Server-side</span>
		<span class="badge">Python Backend</span>
		<span class="badge">Text Prompts</span>
	</div>

	<div class="container">
		<!-- Upload Section -->
		<section class="upload-section">
			<label class="upload-btn" class:disabled={isLoading}>
				<input type="file" accept="image/*" onchange={handleImageSelect} disabled={isLoading} />
				{isLoading && mediaType === 'image' ? 'Processing...' : 'Upload Image'}
			</label>

			<label class="upload-btn video-btn" class:disabled={isLoading}>
				<input type="file" accept="video/*" onchange={handleVideoSelect} disabled={isLoading} />
				{isLoading && mediaType === 'video' ? 'Processing...' : 'Upload Video'}
			</label>

			{#if imageLoaded && mediaType === 'image'}
				<span class="status success">✓ Image ready</span>
			{/if}

			{#if videoMetadata}
				<span class="status success">
					✓ Video: {videoMetadata.frame_count} frames ({formatDuration(videoMetadata.duration)})
				</span>
			{/if}
		</section>

		<!-- Video Timeline -->
		{#if mediaType === 'video' && videoMetadata}
			<section class="video-timeline">
				<div class="timeline-header">
					<span>Frame {currentFrameIndex + 1} / {videoMetadata.frame_count}</span>
					<span class="time">
						{formatDuration((currentFrameIndex / videoMetadata.frame_count) * videoMetadata.duration)}
						/ {formatDuration(videoMetadata.duration)}
					</span>
				</div>

				{#if thumbnails.length > 0}
					<div class="thumbnail-strip">
						{#each thumbnails as thumb}
							<img src={`data:image/jpeg;base64,${thumb}`} alt="thumbnail" />
						{/each}
					</div>
				{/if}

				<input
					type="range"
					min="0"
					max={videoMetadata.frame_count - 1}
					value={currentFrameIndex}
					onchange={handleFrameSlider}
					class="frame-slider"
					disabled={isLoading}
				/>

				<div class="frame-nav">
					<button
						onclick={() => setFrame(Math.max(0, currentFrameIndex - 10))}
						disabled={isLoading || currentFrameIndex === 0}
					>
						-10
					</button>
					<button
						onclick={() => setFrame(Math.max(0, currentFrameIndex - 1))}
						disabled={isLoading || currentFrameIndex === 0}
					>
						Prev
					</button>
					<button
						onclick={() => setFrame(Math.min(videoMetadata.frame_count - 1, currentFrameIndex + 1))}
						disabled={isLoading || currentFrameIndex === videoMetadata.frame_count - 1}
					>
						Next
					</button>
					<button
						onclick={() => setFrame(Math.min(videoMetadata.frame_count - 1, currentFrameIndex + 10))}
						disabled={isLoading || currentFrameIndex === videoMetadata.frame_count - 1}
					>
						+10
					</button>
				</div>
			</section>
		{/if}

		<!-- Prompt Section -->
		{#if imageLoaded}
			<section class="prompt-section">
				<div class="prompt-input">
					<input
						type="text"
						bind:value={textPrompt}
						placeholder="Describe what to segment (e.g., 'cat', 'person', 'red car')"
						onkeydown={handleKeydown}
						disabled={isLoading}
					/>
					<button onclick={segmentWithText} disabled={isLoading || !textPrompt.trim()}>
						{isLoading ? 'Segmenting...' : 'Segment'}
					</button>
				</div>
			</section>
		{/if}

		<!-- Error Display -->
		{#if error}
			<div class="error">
				<strong>Error:</strong>
				{error}
			</div>
		{/if}

		<!-- Image/Frame Display -->
		{#if displayImage}
			<section class="image-section">
				<div class="image-container">
					<img src={displayImage} alt="Media" class="original-image" />

					<!-- Mask Overlay -->
					{#if masks.length > 0 && masks[selectedMaskIndex]}
						<img
							src={`data:image/png;base64,${masks[selectedMaskIndex].mask}`}
							alt="Segmentation mask"
							class="mask-overlay"
						/>
					{/if}
				</div>

				<!-- Mask Selection -->
				{#if masks.length > 1}
					<div class="mask-selector">
						<span>Objects found: {masks.length}</span>
						<div class="mask-buttons">
							{#each masks as mask, i}
								<button
									class="mask-btn"
									class:active={selectedMaskIndex === i}
									onclick={() => (selectedMaskIndex = i)}
								>
									{i + 1}
									{#if mask.score}
										<small>({(mask.score * 100).toFixed(0)}%)</small>
									{/if}
								</button>
							{/each}
						</div>
					</div>
				{:else if masks.length === 1}
					<div class="mask-info">
						<span>1 object found</span>
						{#if masks[0].score}
							<span class="score">Confidence: {(masks[0].score * 100).toFixed(1)}%</span>
						{/if}
					</div>
				{/if}
			</section>
		{/if}

		<!-- Instructions -->
		{#if mediaType === 'none'}
			<section class="instructions">
				<h2>How to use</h2>
				<ol>
					<li>Upload an <strong>image</strong> or <strong>video</strong></li>
					<li>For videos, navigate to the frame you want to segment</li>
					<li>Enter a text description of what you want to segment</li>
					<li>Click "Segment" or press Enter</li>
					<li>View the segmentation mask overlay</li>
				</ol>
				<p class="note">
					Make sure the Python backend is running on <code>localhost:8000</code>
				</p>
				<div class="setup-code">
					<code>cd python && uv run src/main.py</code>
				</div>
			</section>
		{/if}
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
		color: #667eea;
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
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
		margin-bottom: 2rem;
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

	.badge.server {
		background: rgba(102, 126, 234, 0.2);
		color: #667eea;
	}

	.container {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.upload-section {
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.upload-btn {
		display: inline-block;
		padding: 0.75rem 1.5rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 500;
		transition: opacity 0.2s;
	}

	.upload-btn.video-btn {
		background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
	}

	.upload-btn:hover:not(.disabled) {
		opacity: 0.9;
	}

	.upload-btn.disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.upload-btn input {
		display: none;
	}

	.status {
		font-size: 0.875rem;
	}

	.status.success {
		color: #4ade80;
	}

	/* Video Timeline */
	.video-timeline {
		background: #1a1a1a;
		padding: 1rem;
		border-radius: 12px;
	}

	.timeline-header {
		display: flex;
		justify-content: space-between;
		margin-bottom: 0.75rem;
		font-size: 0.875rem;
		color: #888;
	}

	.thumbnail-strip {
		display: flex;
		gap: 2px;
		margin-bottom: 0.5rem;
		overflow: hidden;
		border-radius: 4px;
	}

	.thumbnail-strip img {
		height: 50px;
		flex: 1;
		object-fit: cover;
		opacity: 0.8;
	}

	.frame-slider {
		width: 100%;
		height: 8px;
		-webkit-appearance: none;
		appearance: none;
		background: #333;
		border-radius: 4px;
		outline: none;
		margin-bottom: 0.75rem;
	}

	.frame-slider::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 16px;
		height: 16px;
		background: #667eea;
		border-radius: 50%;
		cursor: pointer;
	}

	.frame-slider::-moz-range-thumb {
		width: 16px;
		height: 16px;
		background: #667eea;
		border-radius: 50%;
		cursor: pointer;
		border: none;
	}

	.frame-nav {
		display: flex;
		gap: 0.5rem;
		justify-content: center;
	}

	.frame-nav button {
		padding: 0.5rem 1rem;
		background: #333;
		color: #fafafa;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.875rem;
	}

	.frame-nav button:hover:not(:disabled) {
		background: #444;
	}

	.frame-nav button:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}

	.prompt-section {
		background: #1a1a1a;
		padding: 1rem;
		border-radius: 12px;
	}

	.prompt-input {
		display: flex;
		gap: 0.75rem;
	}

	.prompt-input input {
		flex: 1;
		padding: 0.75rem 1rem;
		border: 1px solid #333;
		border-radius: 8px;
		background: #0a0a0a;
		color: #fafafa;
		font-size: 1rem;
	}

	.prompt-input input:focus {
		outline: none;
		border-color: #667eea;
	}

	.prompt-input button {
		padding: 0.75rem 1.5rem;
		background: #667eea;
		color: white;
		border: none;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 500;
		transition: background 0.2s;
	}

	.prompt-input button:hover:not(:disabled) {
		background: #5a6fd6;
	}

	.prompt-input button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.error {
		background: #2d1b1b;
		border: 1px solid #7f1d1d;
		color: #fca5a5;
		padding: 1rem;
		border-radius: 8px;
	}

	.image-section {
		background: #1a1a1a;
		padding: 1rem;
		border-radius: 12px;
	}

	.image-container {
		position: relative;
		display: inline-block;
		max-width: 100%;
	}

	.original-image {
		max-width: 100%;
		max-height: 600px;
		border-radius: 8px;
		display: block;
	}

	.mask-overlay {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		border-radius: 8px;
		pointer-events: none;
		mix-blend-mode: screen;
		opacity: 0.7;
	}

	.mask-selector {
		margin-top: 1rem;
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.mask-selector span {
		color: #888;
		font-size: 0.875rem;
	}

	.mask-buttons {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.mask-btn {
		padding: 0.5rem 0.75rem;
		background: #333;
		color: #fafafa;
		border: 1px solid #444;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.875rem;
		transition: all 0.2s;
	}

	.mask-btn:hover {
		background: #444;
	}

	.mask-btn.active {
		background: #667eea;
		border-color: #667eea;
	}

	.mask-btn small {
		opacity: 0.7;
		margin-left: 0.25rem;
	}

	.mask-info {
		margin-top: 1rem;
		display: flex;
		gap: 1rem;
		color: #888;
		font-size: 0.875rem;
	}

	.score {
		color: #4ade80;
	}

	.instructions {
		background: #1a1a1a;
		padding: 1.5rem;
		border-radius: 12px;
	}

	.instructions h2 {
		margin-top: 0;
		font-size: 1.25rem;
	}

	.instructions ol {
		margin: 1rem 0;
		padding-left: 1.5rem;
	}

	.instructions li {
		margin: 0.5rem 0;
		color: #ccc;
	}

	.note {
		color: #888;
		font-size: 0.875rem;
		margin-bottom: 0.75rem;
	}

	.setup-code {
		background: #0a0a0a;
		padding: 0.75rem 1rem;
		border-radius: 6px;
	}

	.setup-code code {
		color: #4ade80;
		font-size: 0.875rem;
	}

	code {
		background: #333;
		padding: 0.2rem 0.4rem;
		border-radius: 4px;
		font-size: 0.875rem;
	}
</style>
