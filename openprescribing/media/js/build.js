let UglifyJS = require("uglify-js");
let browserify = require('browserify');
let watchify = require('watchify');
var fs = require('fs');


let deployDir = '../../static/js'
let inProduction = process.argv[2] == 'production' ? true : false
//let envify = require('envify')
let modules = [
  'global',
  'list-filter',
  'analyse-form',
  'bubble',
  'bar-charts',
  'tariff-charts',
  'measures'
];

let files = modules.map(x => `./src/${x}.js`)
let bundles = modules.map(x => `${deployDir}/${x}.js`)

// Not caching is a condition of watchify
let b = browserify(files, {
  cache: {},
  packageCache: {}
});

// Transforms
b.transform('envify');
if (inProduction) {
  b.transform('uglifyify');
}

// Plugins:
// * `factor-bundle` extracts common code to own file
// * `watchify` observes and re-builds files on changes
b.plugin('factor-bundle', { outputs: bundles }); //
if (!inProduction) {
  b.plugin('watchify');
  b.on('update', bundle);
}

function bundle(ids) {
  if (ids === undefined) {
    // The first time we bundle (i.e. not via watchify)
    console.log(`Updating ${files}`);
  } else {
    console.log(`Updating ${ids}`);
  }
  b.bundle().on(
    'error', function (e) {
      throw e;
    }).pipe(
      fs.createWriteStream(`${deployDir}/common.js`)
    ).on(
      'finish', minify
    );
}

function minify() {
  if (inProduction) {
    modules.push('common');
    for (let m of modules) {
      console.log(`Minifiying ${deployDir}/${m}.js`)
      code = fs.readFileSync(`${deployDir}/${m}.js`, 'utf8');
      var result = UglifyJS.minify(code, {ie8: true});
      if (result.error) throw result.error;
      fs.writeFileSync(`${deployDir}/${m}.min.js`, result.code);
    }
    console.log('Minification complete')
  }
}

bundle();
