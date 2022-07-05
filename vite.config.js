import { viteStaticCopy } from "vite-plugin-static-copy";

/**
 * @type {import('vite').UserConfig}
 */
const config = {
  build: {
    manifest: true,
    rollupOptions: {
      input: "./assets/src/scripts/index.js",
      output: {
        entryFileNames: `dist/[name].js`,
        chunkFileNames: `dist/[name].js`,
        assetFileNames: `dist/[name].[ext]`,
      },
    },
    outDir: "./openprescribing/static/assets",
  },
  plugins: [
    viteStaticCopy({
      targets: [
        {
          src: "node_modules/bootstrap/dist/*",
          dest: "vendor/bootstrap",
        },
        {
          src: "node_modules/jquery/dist/*",
          dest: "vendor/jquery",
        },
        {
          src: "node_modules/@sentry/browser/build/*",
          dest: "vendor/sentry",
        },
        {
          src: "node_modules/domready/ready.min.js",
          dest: "vendor/domready",
        },
        {
          src: "node_modules/bigtext/dist/bigtext.js",
          dest: "vendor/bigtext",
        },
      ],
    }),
  ],
};

export default config;
