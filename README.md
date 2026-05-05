# Gaming Platform

A full-stack web-based gaming platform where players can discover, purchase, and play games directly in their browser. Developers can publish and manage their titles, while admins oversee the platform and its users.

---

## Features

- **Authentication** — Sign up, log in, and manage profiles for players, developers, and admins. Developer accounts require admin verification before activation.
- **Game Discovery** — Browse, filter by genre and platform, and search for games. Each game has a dedicated detail page with media, pricing, reviews, and comments.
- **Shopping & Checkout** — Cart management, Stripe-powered checkout, saved payment cards, and automatic game key delivery via email.
- **Library & Gameplay** — Players can launch and play web-based games they own directly from their library, with automatic playtime tracking.
- **Social** — Reviews with ratings, threaded comments on game pages, and the ability to follow developers.
- **Notifications** — An in-app inbox for players; developers can broadcast announcements to game owners or their followers.
- **Developer Tools** — Full game listing management including version uploads, media uploads, and a revenue/sales dashboard.
- **Admin Tools** — Platform-wide stats, game management, bulk game key uploads, and developer account verification.

---

## User Stories

### Player
- Sign up, log in, log out, and manage profile (avatar, bio, username)
- Browse, filter, and search for games; view game detail pages
- Add games to cart and check out via Stripe; receive a confirmation email with game key(s)
- Access owned games from the library and launch them in-browser; playtime is tracked automatically
- Write and edit reviews with ratings; post and reply to comments on game pages
- Follow or unfollow developers
- View a notification inbox and mark items as read
- Cannot repurchase a game already owned

### Developer
- Register a developer account with company info (subject to admin approval)
- Manage game listings: create, edit, publish, and delete
- Upload game versions and media (screenshots, videos); set the active version
- Post announcements to game owners or followers
- View a dashboard with revenue, sales, and per-game statistics

### Admin
- Verify and activate developer accounts
- View platform-wide stats: users, games, orders, and revenue
- Add, edit, and update any game on the platform
- Add bulk game keys to any listing

---

## Wireframes

UI wireframes for the platform are available in [`wireframe`](./wireframe). Refer to it for screen layouts, navigation flows, and component structure across all three user roles.
