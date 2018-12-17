function formatTableAsCSV(table) {
  return table.map(formatRowAsCSV).join('\n');
}

function formatRowAsCSV(row) {
  return row.map(formatCellAsCSV).join(',');
}

function formatCellAsCSV(cell) {
  cell = cell ? cell.toString() : '';
  if (cell.match(/[,"\r\n]/)) {
    return '"' + cell.replace(/"/g, '""') + '"';
  } else {
    return cell;
  }
}

function getFilename(name) {
  var cleanName = name
    // Remove any chars not on whitelist
    .replace(/[^\w \-\.]/g, '')
    // Replace runs of whitespace with single space
    .replace(/\s+/g, ' ')
    // Trim leading and trailing whitespace
    .replace(/^\s+|\s+$/g, '');
  return cleanName + '.csv';
}

module.exports = {
  formatTableAsCSV: formatTableAsCSV,
  getFilename: getFilename
};
