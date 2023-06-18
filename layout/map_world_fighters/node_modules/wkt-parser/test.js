var test = require('tape');
import compare from 'js-struct-compare';
var wktParser = require('./wkt.build.js');
var fixtures = require('./test-fixtures.json');

fixtures.forEach((item, i)=>{
  test(`fixture ${i + 1}`, t=>{
    var out = wktParser(item.code);
    //console.log(JSON.stringify(out, null, 2));
    const diff = JSON.stringify(compare(item.value, JSON.parse(JSON.stringify(out))), null, 2);
    t.equal(diff, '[]');
    t.end();
  });
})
