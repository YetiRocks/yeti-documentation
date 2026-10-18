// Every book loads clean (YTC-2140). The gate's `test` fails a page on an
// uncaught page error or a console error, so this pins the one that shipped:
// mdBook's stock book.js `themes()` dereferenced `#theme-list`, which this
// app's index.hbs does not render, and threw on every page of every book.
//
// Each book is opened at its root and at the first chapter its sidebar links
// to, so a page deeper than the root is judged too. The sidebar must still be
// shown once book.js runs to its end (the stock sidebar() block hides it under
// this template), and the arrow key the chapter links advertise must work.
import { test, expect } from '@yeti/ui-gate';

const app = process.env.YETI_APP_URL!;
const books = ['learn', 'guides', 'reference'];

for (const book of books) {
  test(`${book}: root and first chapter load without a page error`, async ({ page }) => {
    const root = new URL(`${book}/`, app).toString();
    const resp = await page.goto(root, { waitUntil: 'load' });
    expect(resp!.status(), `${root}: status`).toBeLessThan(400);
    await expect(page.locator('#content')).toBeVisible();
    await expect(page.locator('#sidebar'), `${book}: sidebar shown`).toBeVisible();

    const chapter = await page
      .locator('#sidebar a[href$=".html"]')
      .evaluateAll((as) =>
        as
          .map((a) => (a as HTMLAnchorElement).href)
          .find((h) => !/\/(index|toc|404)\.html$/.test(h)),
      );
    expect(chapter, `${book}: the sidebar links no chapter`).toBeTruthy();
    const deep = await page.goto(chapter!, { waitUntil: 'load' });
    expect(deep!.status(), `${chapter}: status`).toBeLessThan(400);
    await expect(page.locator('#sidebar'), `${chapter}: sidebar shown`).toBeVisible();

    // aria-keyshortcuts="Right" on the next-chapter link: the key follows it.
    const next = await page.locator('a[rel="next"]').first().evaluate(
      (a) => (a as HTMLAnchorElement).href,
    );
    await page.keyboard.press('ArrowRight');
    await page.waitForURL(next);
  });
}
