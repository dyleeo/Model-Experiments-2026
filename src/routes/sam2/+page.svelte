<script>
	// Video state
	let videoFile = $state(null);
	let videoMetadata = $state(null);
	let isUploading = $state(false);

	// Frame state
	let currentFrame = $state(0);
	let frames = $state([]);
	let thumbnails = $state([]);

	// Tracking state
	let trackedObjects = $state([]);
	let selectedObjectId = $state(null);
	let isTracking = $state(false);

	// Prompt state
	let promptMode = $state('point'); // 'point' or 'box'
	let pendingPoints = $state([]);
	let pendingBox = $state(null);

	// API
	const API_URL = 'http://localhost:8001'; // SAM2 backend

	async function handleVideoUpload(event) {
		const file = event.target.files?.[0];
		if (!file) return;

		videoFile = file;
		isUploading = true;

		try {
			const formData = new FormData();
			formData.append('video', file);

			const response = await fetch(`${API_URL}/api/video/upload`, {
				method: 'POST',
				body: formData
			});

			if (!response.ok) throw new Error('Upload failed');

			videoMetadata = await response.json();
			await loadThumbnails();
			await loadFrame(0);
		} catch (e) {
			console.error('Upload error:', e);
		} finally {
			isUploading = false;
		}
	}

	async function loadThumbnails() {
		try {
			const response = await fetch(`${API_URL}/api/video/thumbnails?count=20`);
			if (response.ok) {
				const data = await response.json();
				thumbnails = data.thumbnails || [];
			}
		} catch (e) {
			console.error('Thumbnails error:', e);
		}
	}

	async function loadFrame(index) {
		try {
			const response = await fetch(`${API_URL}/api/video/frame/${index}`);
			if (response.ok) {
				const data = await response.json();
				frames[index] = data.frame;
				currentFrame = index;
			}
		} catch (e) {
			console.error('Frame error:', e);
		}
	}

	async function addObjectToTrack() {
		if (pendingPoints.length === 0 && !pendingBox) return;

		isTracking = true;

		try {
			const response = await fetch(`${API_URL}/api/track/add`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					frame_index: currentFrame,
					points: pendingPoints,
					box: pendingBox
				})
			});

			if (response.ok) {
				const data = await response.json();
				trackedObjects = [...trackedObjects, data.object];
				selectedObjectId = data.object.id;
			}
		} catch (e) {
			console.error('Track error:', e);
		} finally {
			isTracking = false;
			pendingPoints = [];
			pendingBox = null;
		}
	}

	async function propagateTracking() {
		if (trackedObjects.length === 0) return;

		isTracking = true;

		try {
			const response = await fetch(`${API_URL}/api/track/propagate`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ object_ids: trackedObjects.map((o) => o.id) })
			});

			if (response.ok) {
				const data = await response.json();
				// Update tracked objects with propagated masks
				console.log('Propagation complete:', data);
			}
		} catch (e) {
			console.error('Propagation error:', e);
		} finally {
			isTracking = false;
		}
	}

	function formatTime(seconds) {
		const mins = Math.floor(seconds / 60);
		const secs = Math.floor(seconds % 60);
		return `${mins}:${secs.toString().padStart(2, '0')}`;
	}
</script>

<svelte:head>
	<title>SAM 2 - Model Experiments 2026</title>
</svelte:head>

<main>
	<nav class="breadcrumb">
		<a href="/">← Back to experiments</a>
	</nav>

	<h1>SAM 2 Video Segmentation</h1>
	<p class="subtitle">Segment and track anything in videos with streaming memory</p>

	<div class="badge-row">
		<span class="badge server">Server-side</span>
		<span class="badge">44 FPS</span>
		<span class="badge">Video Tracking</span>
		<span class="badge">Temporal Consistency</span>
	</div>

	<div class="container">
		<!-- Upload Section -->
		<section class="upload-section">
			<label class="upload-btn" class:disabled={isUploading}>
				<input type="file" accept="video/*" onchange={handleVideoUpload} disabled={isUploading} />
				{isUploading ? 'Uploading...' : videoFile ? 'Change Video' : 'Upload Video'}
			</label>

			{#if videoMetadata}
				<span class="video-info">
					{videoMetadata.frame_count} frames • {formatTime(videoMetadata.duration)} •
					{videoMetadata.fps.toFixed(1)} FPS
				</span>
			{/if}
		</section>

		{#if videoMetadata}
			<!-- Timeline Section -->
			<section class="timeline-section">
				<div class="timeline-header">
					<span>Frame {currentFrame + 1} / {videoMetadata.frame_count}</span>
					<span>{formatTime((currentFrame / videoMetadata.fps))}</span>
				</div>

				{#if thumbnails.length > 0}
					<div class="thumbnail-strip">
						{#each thumbnails as thumb, i}
							<button
								class="thumbnail"
								class:active={Math.floor((currentFrame / videoMetadata.frame_count) * thumbnails.length) === i}
								onclick={() => loadFrame(Math.floor((i / thumbnails.length) * videoMetadata.frame_count))}
							>
								<img src={`data:image/jpeg;base64,${thumb}`} alt="Frame {i}" />
							</button>
						{/each}
					</div>
				{/if}

				<input
					type="range"
					class="frame-slider"
					min="0"
					max={videoMetadata.frame_count - 1}
					value={currentFrame}
					oninput={(e) => loadFrame(parseInt(e.target.value))}
				/>
			</section>

			<!-- Canvas Section -->
			<section class="canvas-section">
				<div class="canvas-header">
					<div class="mode-buttons">
						<button class="mode-btn" class:active={promptMode === 'point'} onclick={() => (promptMode = 'point')}>
							Point
						</button>
						<button class="mode-btn" class:active={promptMode === 'box'} onclick={() => (promptMode = 'box')}>
							Box
						</button>
					</div>

					<div class="action-buttons">
						<button
							class="action-btn"
							onclick={addObjectToTrack}
							disabled={isTracking || (pendingPoints.length === 0 && !pendingBox)}
						>
							Add Object
						</button>
						<button
							class="action-btn primary"
							onclick={propagateTracking}
							disabled={isTracking || trackedObjects.length === 0}
						>
							{isTracking ? 'Tracking...' : 'Propagate Tracking'}
						</button>
					</div>
				</div>

				<div class="canvas-container">
					{#if frames[currentFrame]}
						<img src={`data:image/jpeg;base64,${frames[currentFrame]}`} alt="Current frame" class="frame-image" />
					{:else}
						<div class="frame-placeholder">
							<p>Loading frame...</p>
						</div>
					{/if}
				</div>

				<div class="instructions">
					{#if promptMode === 'point'}
						<p>Click on the object you want to track. Click multiple points for better accuracy.</p>
					{:else}
						<p>Draw a bounding box around the object you want to track.</p>
					{/if}
				</div>
			</section>

			<!-- Tracked Objects -->
			{#if trackedObjects.length > 0}
				<section class="objects-section">
					<h3>Tracked Objects</h3>
					<div class="objects-list">
						{#each trackedObjects as obj}
							<div class="object-card" class:selected={selectedObjectId === obj.id}>
								<div class="object-color" style="background: {obj.color}"></div>
								<span class="object-name">Object {obj.id}</span>
								<button class="object-remove" onclick={() => (trackedObjects = trackedObjects.filter((o) => o.id !== obj.id))}>
									×
								</button>
							</div>
						{/each}
					</div>
				</section>
			{/if}
		{/if}

		<!-- Instructions -->
		{#if !videoMetadata}
			<section class="info-section">
				<h2>How to Use SAM 2 for Video</h2>
				<ol>
					<li>Upload a video file</li>
					<li>Navigate to a frame where your object is visible</li>
					<li>Click points or draw a box to identify the object</li>
					<li>Click "Add Object" to start tracking</li>
					<li>Click "Propagate Tracking" to segment through the entire video</li>
				</ol>

				<div class="setup-info">
					<h3>Backend Setup</h3>
					<p>SAM 2 requires a Python backend with GPU support.</p>
					<div class="code-block">
						<code>
							# Install SAM 2<br />
							pip install segment-anything-2<br /><br />
							# Run the backend<br />
							cd python && python sam2_server.py
						</code>
					</div>
				</div>
			</section>
		{/if}

		<!-- About Section -->
		<section class="about-section">
			<h2>About SAM 2</h2>
			<div class="about-content">
				<p>
					SAM 2 (Segment Anything Model 2) extends the original SAM to video with a streaming memory architecture.
					It maintains temporal consistency across frames and handles object occlusion and reappearance.
				</p>

				<div class="features-grid">
					<div class="feature">
						<h4>44 FPS</h4>
						<p>Real-time video processing</p>
					</div>
					<div class="feature">
						<h4>3× Fewer Interactions</h4>
						<p>Compared to prior methods</p>
					</div>
					<div class="feature">
						<h4>6× Faster</h4>
						<p>Than original SAM on images</p>
					</div>
					<div class="feature">
						<h4>Streaming Memory</h4>
						<p>Handles long videos efficiently</p>
					</div>
				</div>
			</div>
		</section>
	</div>
</main>

<style>
	main {
		max-width: 1000px;
		margin: 0 auto;
		padding: 2rem;
	}

	.breadcrumb {
		margin-bottom: 1.5rem;
	}

	.breadcrumb a {
		color: #f093fb;
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
		background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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
		background: rgba(240, 147, 251, 0.2);
		color: #f093fb;
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
		padding: 0.75rem 1.5rem;
		background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
		color: white;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 500;
	}

	.upload-btn.disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.upload-btn input {
		display: none;
	}

	.video-info {
		color: #4ade80;
		font-size: 0.875rem;
	}

	.timeline-section {
		background: #1a1a1a;
		padding: 1rem;
		border-radius: 12px;
	}

	.timeline-header {
		display: flex;
		justify-content: space-between;
		margin-bottom: 0.75rem;
		color: #888;
		font-size: 0.875rem;
	}

	.thumbnail-strip {
		display: flex;
		gap: 2px;
		margin-bottom: 0.75rem;
		overflow-x: auto;
	}

	.thumbnail {
		flex-shrink: 0;
		padding: 0;
		border: 2px solid transparent;
		background: none;
		cursor: pointer;
		border-radius: 4px;
		overflow: hidden;
	}

	.thumbnail.active {
		border-color: #f093fb;
	}

	.thumbnail img {
		height: 50px;
		width: auto;
		display: block;
	}

	.frame-slider {
		width: 100%;
		height: 8px;
		-webkit-appearance: none;
		appearance: none;
		background: #333;
		border-radius: 4px;
		outline: none;
	}

	.frame-slider::-webkit-slider-thumb {
		-webkit-appearance: none;
		width: 16px;
		height: 16px;
		background: #f093fb;
		border-radius: 50%;
		cursor: pointer;
	}

	.canvas-section {
		background: #1a1a1a;
		padding: 1rem;
		border-radius: 12px;
	}

	.canvas-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		flex-wrap: wrap;
		gap: 0.75rem;
	}

	.mode-buttons,
	.action-buttons {
		display: flex;
		gap: 0.5rem;
	}

	.mode-btn {
		padding: 0.5rem 1rem;
		background: #2a2a2a;
		border: 1px solid #333;
		color: #fafafa;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.875rem;
	}

	.mode-btn.active {
		background: #f093fb;
		border-color: #f093fb;
	}

	.action-btn {
		padding: 0.5rem 1rem;
		background: #2a2a2a;
		border: 1px solid #333;
		color: #fafafa;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.875rem;
	}

	.action-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.action-btn.primary {
		background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
		border: none;
	}

	.canvas-container {
		background: #0a0a0a;
		border-radius: 8px;
		overflow: hidden;
		min-height: 400px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.frame-image {
		max-width: 100%;
		max-height: 500px;
	}

	.frame-placeholder {
		color: #666;
	}

	.instructions {
		margin-top: 0.75rem;
	}

	.instructions p {
		margin: 0;
		color: #888;
		font-size: 0.875rem;
	}

	.objects-section {
		background: #1a1a1a;
		padding: 1rem;
		border-radius: 12px;
	}

	.objects-section h3 {
		margin: 0 0 0.75rem 0;
		font-size: 1rem;
		color: #888;
	}

	.objects-list {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.object-card {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 0.75rem;
		background: #2a2a2a;
		border: 1px solid #333;
		border-radius: 6px;
	}

	.object-card.selected {
		border-color: #f093fb;
	}

	.object-color {
		width: 12px;
		height: 12px;
		border-radius: 50%;
	}

	.object-name {
		font-size: 0.875rem;
	}

	.object-remove {
		background: none;
		border: none;
		color: #888;
		cursor: pointer;
		font-size: 1.25rem;
		line-height: 1;
		padding: 0;
	}

	.object-remove:hover {
		color: #f87171;
	}

	.info-section {
		background: #1a1a1a;
		padding: 1.5rem;
		border-radius: 12px;
	}

	.info-section h2 {
		margin: 0 0 1rem 0;
	}

	.info-section ol {
		padding-left: 1.5rem;
		color: #aaa;
	}

	.info-section li {
		margin: 0.5rem 0;
	}

	.setup-info {
		margin-top: 1.5rem;
	}

	.setup-info h3 {
		margin: 0 0 0.5rem 0;
		font-size: 1rem;
		color: #888;
	}

	.setup-info p {
		color: #888;
		margin: 0 0 0.75rem 0;
	}

	.code-block {
		background: #0a0a0a;
		padding: 1rem;
		border-radius: 8px;
	}

	.code-block code {
		color: #4ade80;
		font-size: 0.875rem;
		line-height: 1.6;
	}

	.about-section {
		background: #1a1a1a;
		padding: 1.5rem;
		border-radius: 12px;
	}

	.about-section h2 {
		margin: 0 0 1rem 0;
	}

	.about-content p {
		color: #aaa;
		line-height: 1.6;
		margin: 0 0 1.5rem 0;
	}

	.features-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 1rem;
	}

	.feature {
		background: #0a0a0a;
		padding: 1rem;
		border-radius: 8px;
		text-align: center;
	}

	.feature h4 {
		margin: 0 0 0.25rem 0;
		color: #f093fb;
	}

	.feature p {
		margin: 0;
		color: #888;
		font-size: 0.875rem;
	}
</style>
