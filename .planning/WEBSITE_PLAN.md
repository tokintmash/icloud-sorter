# Website + Purchase Link Plan for iCloud Photo Sorter

## Summary

Build a simple WordPress marketing site and keep checkout outside WordPress using Lemon Squeezy hosted checkout. The website's job is to explain the product, qualify buyers, and send every purchase CTA through one controlled redirect path so checkout links, attribution, and post-purchase behavior stay easy to manage.

This plan assumes:
- WordPress is used only for content and CTA routing
- Lemon Squeezy handles payment, tax/VAT, and purchase email
- Buyers receive a thank-you page plus email with the latest Windows download link
- In-app license enforcement is not required for the first paid website launch
- `Buy Now` should only go live once a packaged Windows build exists

## Key Changes

### Site structure

Create these WordPress pages:
- `/` Home: value prop, screenshots, primary CTA
- `/how-it-works/`: 3-step explanation matching the repo's sorter flow
- `/prerequisites/`: Windows 10/11, iCloud for Windows installed and synced, local photos already present
- `/faq/`: safety, duplicates, moved-vs-copied behavior, unsupported cases
- `/support/`: contact and troubleshooting path
- `/purchase/success/`: post-checkout landing page
- `/purchase/cancelled/`: recovery page after abandoned checkout

Keep the public nav minimal:
- Home
- How It Works
- Prerequisites
- FAQ
- Support
- Buy Now

### Purchase link logic

Use one canonical purchase entrypoint on the site:
- `/buy/`

All CTA buttons on WordPress should link to `/buy/?src=<placement>`
Examples:
- `/buy/?src=hero`
- `/buy/?src=pricing`
- `/buy/?src=faq`
- `/buy/?src=footer`

`/buy/` should immediately redirect to the Lemon Squeezy checkout URL and append tracking context:
- preserve `src`
- add standard UTM params
- optionally allow `coupon` passthrough later

Implementation shape:
- Store the Lemon Squeezy checkout URL once in WordPress settings or theme config
- Render all CTAs from one reusable button block/shortcode/template partial
- Never hardcode raw Lemon Squeezy links into multiple pages

Recommended redirect contract:
- Input query params: `src`, optional `coupon`
- Success redirect target: `/purchase/success/?src=<placement>`
- Cancel redirect target: `/purchase/cancelled/?src=<placement>`

### Post-purchase fulfillment

Use "thank-you page + email" fulfillment:
- Lemon Squeezy sends receipt email
- Success page thanks the buyer, reminds them of prerequisites, and repeats the download button
- Download button points to a managed download URL, not scattered release links

Use one managed download endpoint:
- `/download/`

`/download/` should redirect to the current packaged Windows release URL. Manage that target in one WordPress setting so new releases only require one update.

Initial visibility rules:
- `/download/` is not linked from the public nav
- It is shown on `/purchase/success/`
- It is included in the post-purchase email copy
- If you later add free trials, the same endpoint can become public without restructuring the site

### Beta and release distribution options

Immediate demo/beta path:
- Use a separate public GitHub releases repo as the first public download surface
- Keep the main product repo private
- Publish packaged beta builds from CI into the public releases repo
- Point the WordPress site's demo download button to either the public release asset directly or to the site's managed `/download/` redirect
- This path is optimized for getting a beta and landing page online quickly

Deferred later-phase options:
- GitHub Action publishes release assets to the public releases repo and WordPress only stores page content and links
- GitHub Action updates WordPress release metadata through the WordPress REST API so the site can show latest version and version history automatically
- GitHub Action uploads binaries directly to the web host over SFTP/SSH and WordPress links to host-local files
- WordPress stores release entries only, while binaries remain hosted in a separate public location
- A small WordPress plugin or custom post type can be added later to manage release history, latest-version badges, and download CTA rendering

### Messaging and content direction

Position the app as:
- Windows utility for people using iCloud Photos on Windows
- Solves the flat-folder problem without re-downloading files
- Works with albums already created on iPhone/iCloud
- Moves files in place inside the iCloud Photos folder

Each page should reinforce these trust points:
- No downloading from iCloud during sorting
- Uses Apple login with 2FA
- Works on locally synced files
- Users should back up photos before major reorganization
- Unofficial tool, not affiliated with Apple

## Public Interfaces

Use these site-level interfaces as the stable contract:
- `/buy/`
  - accepts `src`
  - optional future support for `coupon`
  - always redirects to Lemon Squeezy
- `/purchase/success/`
  - displays confirmation, prerequisites reminder, support link, and download CTA
- `/purchase/cancelled/`
  - explains nothing was charged/completed and gives a retry CTA
- `/download/`
  - single managed redirect to the latest Windows build

Operational data to manage centrally in WordPress:
- `checkout_url`
- `download_url`
- `support_email`
- `current_version`
- optional `launch_enabled` flag to switch public CTA from "Join waitlist / Coming soon" to "Buy Now"

Optional later-phase release metadata in WordPress:
- `latest_version`
- `latest_download_url`
- `release_notes_excerpt`
- `release_published_at`
- optional release archive entries for a public version history page

## Test Plan

Validate these scenarios before launch:
- Every site CTA routes through `/buy/` and lands on the correct Lemon Squeezy checkout
- `src` values survive the redirect chain and can be read in analytics
- Successful purchase returns to `/purchase/success/`
- Cancelled checkout returns to `/purchase/cancelled/`
- `/download/` redirects to the current Windows release and is easy to update for a new version
- Success page contains prerequisites, support contact, and download CTA
- Mobile layout works for hero, screenshots, FAQ, and checkout CTA sections
- Broken or disabled `launch_enabled` state hides purchase CTAs and shows a waitlist/coming-soon CTA instead

Validate these scenarios in the later release-automation phase:
- GitHub release publication updates the public beta/download target without manual file uploads
- The WordPress site can show the latest version at the top if release metadata automation is added
- Version history ordering remains newest-first after repeated releases
- Demo/beta links continue working even if the website content is updated separately from releases

## Assumptions

- WordPress is the CMS, not the checkout engine
- Lemon Squeezy is the merchant-of-record and checkout provider
- First paid version delivers access via download link and email, not license activation
- Packaging must be completed before enabling purchase
- Licensing, keys, and in-app activation remain a later phase and should not block the website launch
- The first public demo/beta will use a separate public GitHub releases repo unless a better hosting target is chosen later
- The exact later-phase release automation method for WordPress remains intentionally undecided
