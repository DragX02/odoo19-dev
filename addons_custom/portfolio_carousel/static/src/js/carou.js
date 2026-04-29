/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

class Carousel3D {
    constructor(container, options) {
        this.container = container;
        this.options = Object.assign({
            depth: 300,
            interval: 3000,
            autoplay: true,
            fallback: "/portfolio_carousel/static/description/fallback.svg",
        }, options || {});
        this.angle = 0;
        this.timer = null;
        this.paused = false;
        this.imgs = Array.from(this.container.querySelectorAll("img")).map(img => img.getAttribute("src")).filter(src => src);
        if (this.imgs.length > 0) this.init();
    }
    init() {
        if (this.imgs.length === 0) return;
        this.container.innerHTML = "";
        this.spinner = document.createElement("div");
        this.spinner.classList.add("o_carousel3d_spinner");
        this.container.appendChild(this.spinner);
        const angleStep = 360 / this.imgs.length;
        this.imgs.forEach((src, i) => {
            const div = document.createElement("div");
            div.classList.add("item-3d");
            div.style.transform = `rotateY(${angleStep * i}deg) translateZ(${this.options.depth}px)`;
            const img = document.createElement("img");
            img.src = src;
            img.onerror = () => { img.src = this.options.fallback; };
            div.appendChild(img);
            this.spinner.appendChild(div);
        });
        this.renderControls();
        if (this.options.autoplay) this.startAuto();
    }
    renderControls() {
        const nav = document.createElement("div");
        nav.classList.add("nav-3d");
        nav.appendChild(this.createBtn("\u25C0", () => this.rotate(-1)));
        nav.appendChild(this.createBtn("\u23F8", (e) => this.toggle(e.target)));
        nav.appendChild(this.createBtn("\u25B6", () => this.rotate(1)));
        this.container.appendChild(nav);
    }
    createBtn(text, clickHandler) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.textContent = text;
        btn.addEventListener("click", clickHandler);
        return btn;
    }
    rotate(dir) {
        const step = 360 / this.imgs.length;
        this.angle += step * dir;
        if (this.spinner) this.spinner.style.transform = `rotateY(${this.angle}deg)`;
    }
    startAuto() {
        this.timer = setInterval(() => { if (!this.paused) this.rotate(1); }, this.options.interval);
    }
    toggle(btn) {
        this.paused = !this.paused;
        btn.textContent = this.paused ? "\u25B6" : "\u23F8";
    }
    destroy() {
        if (this.timer) clearInterval(this.timer);
    }
}

publicWidget.registry.PortfolioCarousel3D = publicWidget.Widget.extend({
    selector: ".o_carousel3d",
    disabledInEditableMode: false,
    start() {
        const dataset = this.el.dataset;
        this._carousel = new Carousel3D(this.el, {
            depth: parseInt(dataset.c3dDepth, 10) || 300,
            interval: parseInt(dataset.c3dInterval, 10) || 3000,
            autoplay: dataset.c3dAutoplay !== "false",
        });
        return this._super.apply(this, arguments);
    },
    destroy() {
        if (this._carousel) this._carousel.destroy();
        this._super.apply(this, arguments);
    },
});