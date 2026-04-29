/** @odoo-module **/
import {registry} from "@web/core/registry";

registry.category("website_snippets").add("s_portfolio_carousel", {
    label: "Portfolio Carousel 3D",
    template: "portfolio_carousel.s_portfolio_carousel",
    thumbnail: "/portfolio_carousel/static/description/snippet_thumbnail.svg",
    category: "content",
    priority: 50,
});
