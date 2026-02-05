<script>
	import favicon from '$lib/assets/favicon.svg';
	import { page } from '$app/stores';

	let { children } = $props();

	// Check if we're on the home page
	let isHome = $derived($page.url.pathname === '/');
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{@render children()}

<style>
	:global(*) {
		box-sizing: border-box;
	}

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
		line-height: 1.5;
	}

	:global(a) {
		color: inherit;
	}

	:global(button) {
		font-family: inherit;
	}

	:global(code) {
		font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
	}

	:global(::selection) {
		background: rgba(102, 126, 234, 0.3);
	}

	:global(::-webkit-scrollbar) {
		width: 8px;
		height: 8px;
	}

	:global(::-webkit-scrollbar-track) {
		background: #1a1a1a;
	}

	:global(::-webkit-scrollbar-thumb) {
		background: #333;
		border-radius: 4px;
	}

	:global(::-webkit-scrollbar-thumb:hover) {
		background: #444;
	}
</style>
