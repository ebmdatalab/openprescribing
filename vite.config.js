// import legacy from "@vitejs/plugin-legacy";
import copy from "rollup-plugin-copy";

/**
 * @type {import('vite').UserConfig}
 */
const config = {
  base: "/static/bundler/",
  build: {
    manifest: true,
    rollupOptions: {
      input: {
        "analyse-form": "openprescribing/media/js/src/analyse-form.js",
        "bar-charts": "openprescribing/media/js/src/bar-charts.js",
        "config": "openprescribing/media/js/src/config.js", // TODO: this doesn't work
        "dmd-advanced-search": "openprescribing/media/js/src/dmd-advanced-search.js",
        "list-filter": "openprescribing/media/js/src/list-filter.js",
        "spending-chart": "openprescribing/media/js/src/spending-chart.js",
        "tariff-charts": "openprescribing/media/js/src/tariff-charts.js",
        bubble: "openprescribing/media/js/src/bubble.js",
        global: "openprescribing/media/js/src/global.js",
        measures: "openprescribing/media/js/src/measures.js",
        index: "openprescribing/media/js/src/css.js",
      },
    },
    outDir: "openprescribing/static/bundler",
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
          src: "./node_modules/bootstrap/dist/css/bootstrap.min*",
          dest: "./openprescribing/static/vendor/bootstrap/css",
        },
        {
          src: "./node_modules/bootstrap/dist/js/bootstrap.min.js",
          dest: "./openprescribing/static/vendor/bootstrap/js",
        },
        {
          src: "./node_modules/bootstrap/dist/fonts/*",
          dest: "./openprescribing/static/vendor/bootstrap/fonts",
        },
        {
          src: "./node_modules/bootstrap-select/dist/css/bootstrap-select.min.css",
          dest: "./openprescribing/static/vendor/bootstrap-select/",
        },
        {
          src: "./node_modules/bootstrap-datepicker/dist/css/bootstrap-datepicker3.min.css",
          dest: "./openprescribing/static/vendor/bootstrap-select/",
        },
        {
          src: "./node_modules/jQuery-QueryBuilder/dist/css/query-builder.default.min.css",
          dest: "./openprescribing/static/vendor/query-builder/",
        },
        {
          src: "./node_modules/jQuery-QueryBuilder/dist/js/query-builder.standalone.js",
          dest: "./openprescribing/static/vendor/query-builder/",
        },
        {
          src: "./node_modules/datatables.net-bs/css/dataTables.bootstrap.css",
          dest: "./openprescribing/static/vendor/datatables/",
        },
        {
          src: "./node_modules/datatables.net/js/jquery.dataTables.min.js",
          dest: "./openprescribing/static/vendor/datatables/",
        },
        {
          src: "./node_modules/datatables.net-bs/js/dataTables.bootstrap.js",
          dest: "./openprescribing/static/vendor/datatables/",
        },
        {
          src: "./node_modules/jquery/dist/jquery.min*",
          dest: "./openprescribing/static/vendor/jquery/",
        },
        {
          src: "./node_modules/select2/dist/css/select2.min.css",
          dest: "./openprescribing/static/vendor/select2/",
        },
        {
          src: "./node_modules/select2/dist/js/select2.full.min.js",
          dest: "./openprescribing/static/vendor/select2/",
        },
        {
          src: "./node_modules/bigtext/dist/bigtext.js",
          dest: "./openprescribing/static/vendor/bigtext/",
        },
        {
          src: "./node_modules/nouislider/distribute/jquery.nouislider.min.css",
          dest: "./openprescribing/static/vendor/nouislider/",
        },
        {
          src: "./node_modules/nouislider/distribute/jquery.nouislider.pips.min.css",
          dest: "./openprescribing/static/vendor/nouislider/",
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
