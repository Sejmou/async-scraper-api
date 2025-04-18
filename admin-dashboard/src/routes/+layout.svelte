<script lang="ts">
	import { page } from '$app/state';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb';
	import '../app.css';
	let { children, data } = $props();

	const titleCase = (str: string) => str[0].toUpperCase() + str.slice(1);

	const breadCrumbsNameOverrides: Record<string, string> = {
		'spotify-api': 'Spotify API',
		'spotify-internal': 'Internal (unofficial) Spotify APIs',
		'duckdb-demo': 'DuckDB Demo',
		'artist-albums': 'Artist Albums',
		'related-artists': 'Related Artists',
		'dummy-api': 'Dummy API'
	};

	let subroutes = $derived(page.route.id?.split('/').filter(Boolean) || []);
	let subroutesAndLinks = $derived(
		subroutes.map((_, i) => {
			let link = '/' + subroutes.slice(0, i + 1).join('/');
			let subRoutePathComponent = subroutes[i];
			if (subRoutePathComponent === '[taskId]') {
				if (data.task) {
					subRoutePathComponent = `${data.task.id}`;
				} else {
					subRoutePathComponent = 'Unknown Task';
				}
			} else if (subRoutePathComponent === '[dataSource]') {
				if (page.params.dataSource) {
					subRoutePathComponent = page.params.dataSource;
				} else {
					subRoutePathComponent = 'Unknown Data Source';
				}
			} else if (subRoutePathComponent === '[taskType]') {
				if (page.params.taskType) {
					subRoutePathComponent = page.params.taskType;
				} else {
					subRoutePathComponent = 'Unknown Task Type';
				}
			} else if (subRoutePathComponent === '[scraperId]') {
				if (data.scraper) {
					subRoutePathComponent = `Scraper ${data.scraper.id} (${data.scraper.host}:${data.scraper.port})`;
				} else {
					subRoutePathComponent = 'Unknown Scraper';
				}
			}
			link = link.replace('[taskId]', `${data?.task?.id ?? ''}`);
			link = link.replace('[dataSource]', `${page.params?.dataSource ?? ''}`);
			link = link.replace('[taskType]', `${page.params?.taskType ?? ''}`);
			link = link.replace('[scraperId]', `${data?.scraper?.id ?? ''}`);
			return {
				name: breadCrumbsNameOverrides[subRoutePathComponent] || titleCase(subRoutePathComponent),
				link
			};
		})
	);
	let level = $derived(subroutes.length);
</script>

<main class="mx-auto flex max-w-screen-lg flex-col gap-2 p-4 pt-8">
	{#if level > 0}
		<Breadcrumb.Root>
			<Breadcrumb.List>
				<Breadcrumb.Item>
					<Breadcrumb.Link href="/">Home</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator />
				{#each subroutesAndLinks as { name, link }, i}
					<Breadcrumb.Item>
						<Breadcrumb.Link href={link}>{name}</Breadcrumb.Link>
					</Breadcrumb.Item>
					{#if i < subroutesAndLinks.length - 1}
						<Breadcrumb.Separator />
					{/if}
				{/each}
			</Breadcrumb.List>
		</Breadcrumb.Root>
	{/if}
	{@render children()}
</main>
