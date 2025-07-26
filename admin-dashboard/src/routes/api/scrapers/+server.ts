import { db } from '$lib/server/db';
import {
  scraperServerTbl,
} from '$lib/server/db/schema';
import { json } from '@sveltejs/kit';

export async function GET() {
  return json(await db.select().from(scraperServerTbl));
}