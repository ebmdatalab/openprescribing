function getConfig() {
  var config = {};
  if (typeof process.env.API_HOST === 'undefined') {
    config.apiHost = '';
  } else {
    config.apiHost = process.env.API_HOST;
  }
  return config;
}
module.exports = getConfig();
