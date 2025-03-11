<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Textarea } from '$lib/components/ui/textarea';
	import { enhance } from '$app/forms';
	import { Label } from '$lib/components/ui/label';
</script>

<form
	method="POST"
	action="?/batch-import"
	use:enhance={() => {
		return async ({ update }) => {
			await update();
		};
	}}
>
	<div class="grid w-full gap-1.5">
		<Label for="scraper-urls">Base URLs</Label>
		<Textarea name="scraper-urls" placeholder="http://192.0.2.1:8000" id="scraper-urls" />
		<p class="text-muted-foreground text-sm">
			Add one URL per line. Please include protocol (http/https), domain, and port.
		</p>
	</div>
	<Button type="submit" class="mt-2">Import</Button>
</form>
