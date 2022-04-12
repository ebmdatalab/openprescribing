// import legacy from "@vitejs/plugin-legacy";
import copy from "rollup-plugin-copy";

/**
 * @type {import('vite').UserConfig}
 */
const config = {
  base: "/static/",
  build: {
    manifest: false,
    rollupOptions: {
      input: {
        // "analyse-form": "openprescribing/media/js/src/analyse-form.js",
        "bar-charts": "openprescribing/media/js/src/bar-charts.js",
        "config": "openprescribing/media/js/src/config.js", // TODO: this doesn't work
        "dmd-advanced-search": "openprescribing/media/js/src/dmd-advanced-search.js",
        "list-filter": "openprescribing/media/js/src/list-filter.js",
        "spending-chart": "openprescribing/media/js/src/spending-chart.js",
        "tariff-charts": "openprescribing/media/js/src/tariff-charts.js",
        bubble: "openprescribing/media/js/src/bubble.js",
        global: "openprescribing/media/js/src/global.js",
        // measures: "openprescribing/media/js/src/measures.js",
        index: "openprescribing/media/js/src/css.js",
      },
      output: {
        entryFileNames: `js/[name].js`,
        chunkFileNames: `js/[name].js`,
        assetFileNames: `[ext]/[name].[ext]`,
      },
    },
    outDir: "openprescribing/static",
    assetsDir: "",
    emptyOutDir: false,
  },
  clearScreen: false,
  plugins: [
    copy({
      targets: [
        {
          src: "./node_modules/clipboard/dist/clipboard.min.js",
          dest: "./openprescribing/static/js",
        },
        {
          src: "./node_modules/clipboard/dist/clipboard.min.js",
          dest: "./openprescribing/static/js",
        },
      ],
      hook: "writeBundle",
    })
  ],
  test: {
    environment: 'happy-dom',
  },
};

export default config;
