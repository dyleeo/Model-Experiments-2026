<script>
	const experiments = [
		{
			id: 'sam3',
			name: 'SAM 3',
			description: 'Segment Anything Model 3 with text prompts - server-side inference',
			runtime: 'Server (Python)',
			features: ['Text-based prompting', 'Open vocabulary', 'Concept segmentation'],
			status: 'ready',
			gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
		},
		{
			id: 'sam2',
			name: 'SAM 2',
			description: 'Segment Anything Model 2 for video - streaming memory architecture',
			runtime: 'Server (Python)',
			features: ['Video segmentation', '44 FPS real-time', 'Temporal consistency'],
			status: 'demo',
			gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
		},
		{
			id: 'mobilesam',
			name: 'MobileSAM',
			description: 'Lightweight SAM for browser - runs entirely client-side with WebGPU',
			runtime: 'Browser (WebGPU)',
			features: ['9.66M parameters', 'Point/box prompts', 'No server needed'],
			status: 'demo',
			gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
		},
		{
			id: 'yolo',
			name: 'YOLOv8',
			description: 'Real-time object detection and instance segmentation in browser',
			runtime: 'Browser (WebGPU)',
			features: ['Detection + segmentation', '100+ FPS possible', '80 COCO classes'],
			status: 'demo',
			gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
		},
		{
			id: 'fastsam',
			name: 'FastSAM',
			description: 'CNN-based fast segmentation - YOLOv8-seg backbone',
			runtime: 'Browser (WebGPU)',
			features: ['10-100x faster than SAM', 'All prompts supported', 'Lightweight'],
			status: 'demo',
			gradient: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)'
		}
	];
</script>

<svelte:head>
	<title>Model Experiments 2026</title>
</svelte:head>

<main>
	<header>
		<h1>Model Experiments 2026</h1>
		<p class="subtitle">
			Exploring real-time segmentation & detection models - server-side and browser-based
		</p>
	</header>

	<section class="experiments-grid">
		{#each experiments as exp}
			<a href="/{exp.id}" class="experiment-card">
				<div class="card-header" style="background: {exp.gradient}">
					<span class="runtime-badge">{exp.runtime}</span>
					<h2>{exp.name}</h2>
				</div>
				<div class="card-body">
					<p class="description">{exp.description}</p>
					<ul class="features">
						{#each exp.features as feature}
							<li>{feature}</li>
						{/each}
					</ul>
					<div class="card-footer">
						<span class="status" class:ready={exp.status === 'ready'}>
							{exp.status === 'ready' ? 'Ready' : 'Demo'}
						</span>
						<span class="arrow">→</span>
					</div>
				</div>
			</a>
		{/each}
	</section>

	<section class="info-section">
		<h2>About This Project</h2>
		<div class="info-grid">
			<div class="info-card">
				<h3>Server-Side Models</h3>
				<p>
					SAM 2 and SAM 3 run on a Python backend with GPU acceleration. These offer the highest
					quality segmentation but require a running server.
				</p>
				<code>cd python && uv run src/main.py</code>
			</div>
			<div class="info-card">
				<h3>Browser-Based Models</h3>
				<p>
					MobileSAM, YOLOv8, and FastSAM run entirely in your browser using WebGPU. No server
					required - your data stays private.
				</p>
				<code>WebGPU + ONNX Runtime</code>
			</div>
		</div>
	</section>

	<section class="comparison-section">
		<h2>Model Comparison</h2>
		<div class="table-wrapper">
			<table>
				<thead>
					<tr>
						<th>Model</th>
						<th>Runtime</th>
						<th>Speed</th>
						<th>Quality</th>
						<th>Best For</th>
					</tr>
				</thead>
				<tbody>
					<tr>
						<td>SAM 3</td>
						<td>Server</td>
						<td>~30ms/image</td>
						<td>Excellent</td>
						<td>Text-based concept segmentation</td>
					</tr>
					<tr>
						<td>SAM 2</td>
						<td>Server</td>
						<td>44 FPS</td>
						<td>Excellent</td>
						<td>Video segmentation with tracking</td>
					</tr>
					<tr>
						<td>MobileSAM</td>
						<td>Browser</td>
						<td>5-15 FPS</td>
						<td>Good</td>
						<td>Interactive point/box prompts</td>
					</tr>
					<tr>
						<td>YOLOv8</td>
						<td>Browser</td>
						<td>30+ FPS</td>
						<td>Good</td>
						<td>Detection + instance segmentation</td>
					</tr>
					<tr>
						<td>FastSAM</td>
						<td>Browser</td>
						<td>20+ FPS</td>
						<td>Good</td>
						<td>Fast all-instance segmentation</td>
					</tr>
				</tbody>
			</table>
		</div>
	</section>
</main>

<style>
	:global(body) {
		margin: 0;
		font-family:
			-apple-system,
			BlinkMacSystemFont,
			'Segoe UI',
			Roboto,
			sans-serif;
		background: #0a0a0a;
		color: #fafafa;
		min-height: 100vh;
	}

	main {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
	}

	header {
		text-align: center;
		margin-bottom: 3rem;
	}

	h1 {
		font-size: 3rem;
		font-weight: 800;
		margin: 0;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}

	.subtitle {
		color: #888;
		font-size: 1.125rem;
		margin-top: 0.75rem;
	}

	h2 {
		margin-top: 0;
	}

	/* Experiments Grid */
	.experiments-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
		gap: 1.5rem;
		margin-bottom: 3rem;
	}

	.experiment-card {
		background: #1a1a1a;
		border-radius: 16px;
		overflow: hidden;
		text-decoration: none;
		color: inherit;
		transition: transform 0.2s, box-shadow 0.2s;
		border: 1px solid #2a2a2a;
	}

	.experiment-card:hover {
		transform: translateY(-4px);
		box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
	}

	.card-header {
		padding: 1.5rem;
		position: relative;
	}

	.card-header h2 {
		font-size: 1.5rem;
		font-weight: 700;
		margin: 0;
		color: white;
		text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
	}

	.runtime-badge {
		position: absolute;
		top: 1rem;
		right: 1rem;
		background: rgba(0, 0, 0, 0.3);
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-size: 0.75rem;
		font-weight: 500;
		color: white;
	}

	.card-body {
		padding: 1.5rem;
	}

	.description {
		color: #aaa;
		margin: 0 0 1rem 0;
		line-height: 1.5;
	}

	.features {
		list-style: none;
		padding: 0;
		margin: 0 0 1rem 0;
	}

	.features li {
		color: #888;
		font-size: 0.875rem;
		padding: 0.25rem 0;
	}

	.features li::before {
		content: '→ ';
		color: #667eea;
	}

	.card-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding-top: 1rem;
		border-top: 1px solid #2a2a2a;
	}

	.status {
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		color: #888;
		padding: 0.25rem 0.75rem;
		background: #2a2a2a;
		border-radius: 4px;
	}

	.status.ready {
		color: #4ade80;
		background: rgba(74, 222, 128, 0.1);
	}

	.arrow {
		font-size: 1.25rem;
		color: #667eea;
		transition: transform 0.2s;
	}

	.experiment-card:hover .arrow {
		transform: translateX(4px);
	}

	/* Info Section */
	.info-section {
		margin-bottom: 3rem;
	}

	.info-section h2 {
		font-size: 1.5rem;
		margin-bottom: 1.5rem;
	}

	.info-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 1.5rem;
	}

	.info-card {
		background: #1a1a1a;
		padding: 1.5rem;
		border-radius: 12px;
		border: 1px solid #2a2a2a;
	}

	.info-card h3 {
		margin: 0 0 0.75rem 0;
		font-size: 1.125rem;
		color: #fafafa;
	}

	.info-card p {
		color: #888;
		margin: 0 0 1rem 0;
		line-height: 1.5;
	}

	.info-card code {
		display: block;
		background: #0a0a0a;
		padding: 0.75rem;
		border-radius: 6px;
		font-size: 0.875rem;
		color: #4ade80;
	}

	/* Comparison Table */
	.comparison-section h2 {
		font-size: 1.5rem;
		margin-bottom: 1.5rem;
	}

	.table-wrapper {
		overflow-x: auto;
		background: #1a1a1a;
		border-radius: 12px;
		border: 1px solid #2a2a2a;
	}

	table {
		width: 100%;
		border-collapse: collapse;
	}

	th,
	td {
		padding: 1rem;
		text-align: left;
		border-bottom: 1px solid #2a2a2a;
	}

	th {
		background: #0a0a0a;
		font-weight: 600;
		color: #888;
		font-size: 0.875rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	tr:last-child td {
		border-bottom: none;
	}

	tr:hover td {
		background: rgba(102, 126, 234, 0.05);
	}

	td {
		color: #ccc;
	}

	td:first-child {
		font-weight: 600;
		color: #fafafa;
	}

	@media (max-width: 768px) {
		h1 {
			font-size: 2rem;
		}

		.experiments-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
