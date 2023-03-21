const svelte = require('rollup-plugin-svelte');
const resolve = require('@rollup/plugin-node-resolve');

const componentRollupConfig = (src, dest, name) => ({
  input: src,
  output: {
    file: dest,
    format: 'iife',
    name: name,
  },
  plugins: [
    svelte({
      include: 'src/**/*.svelte',
    }),
    resolve({ browser: true }),
  ],
});

module.exports = [
  componentRollupConfig('src/SlimeChat.svelte', 'static/js/svelte/SlimeChat.js', 'SlimeChat'),
];