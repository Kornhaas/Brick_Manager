/* Exercise the actual dashboard quantity controller with deferred fetches. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('brick_manager/static/js/detail_quantities.js', 'utf8');
const flush = () => new Promise(resolve => setImmediate(resolve));
function fixture() {
  const handlers = {}, requests = [];
  function node(dataset = {}) { return {dataset,hidden:false,textContent:'',value:'',listeners:{},classList:{remove(){},add(){}},setAttribute(name,value){this[name]=value;},addEventListener(name,fn){this.listeners[name]=fn;}}; }
  const table=node(), feedback=node(), status=node(), retry=node();
  const input=node({id:'1',partType:'minifig',original:'1'}); input.value='1'; input.matches=selector => selector==='.update-quantity'; table.contains=target => target===input;
  const document={getElementById:id=>({'detailsTable':table,'feedback':feedback,'quantity-status':status,'quantity-retry':retry}[id]),addEventListener:(name,fn)=>handlers[name]=fn};
  const fetch=(url,options)=>new Promise((resolve,reject)=>requests.push({url,options,resolve,reject}));
  vm.runInNewContext(source,{document,fetch,Map,Set,Number,JSON,console}); handlers.DOMContentLoaded();
  return {input,feedback,status,retry,requests,change(value){input.value=value;handlers.input({target:input});},ok(index,value){requests[index].resolve({ok:true,json:async()=>({updates:[{part_id:1,part_type:'minifig',have_quantity:value}]})});},fail(index){requests[index].reject(new Error('offline'));}};
}
(async()=>{
 const t=fixture();t.change('2');t.change('7');
 assert.equal(t.requests.length,1,'only one request may be in flight');
 assert.equal(JSON.parse(t.requests[0].options.body).changes[0].part_type,'minifig');
 t.ok(0,2);await flush();
 assert.equal(t.input.value,'7','old response must not overwrite newer intent');
 assert.equal(t.requests.length,2);t.ok(1,7);await flush();assert.equal(t.input.dataset.original,'7');assert.equal(t.feedback.dataset.state,'saved');
 const d=fixture();d.change('1.9');await flush();assert.equal(d.requests.length,0);assert.equal(d.input.value,'1.9');assert.equal(d.feedback.dataset.state,'invalid');
 const c=fixture();c.change('999');c.ok(0,5);await flush();assert.equal(c.input.value,'5');assert.equal(c.input.dataset.original,'5');
 const r=fixture();r.change('3');r.fail(0);await flush();assert.equal(r.feedback.dataset.state,'error');assert.equal(r.input.value,'3');assert.equal(r.retry.hidden,false);r.retry.listeners.click();assert.equal(r.requests.length,2);r.ok(1,3);await flush();assert.equal(r.feedback.dataset.state,'saved');
 const v=fixture();v.change('2');v.change('1');v.ok(0,2);await flush();assert.equal(v.requests.length,2,'reverting while a save is in flight still must be persisted');v.ok(1,1);await flush();assert.equal(v.input.dataset.original,'1');
 console.log('PASS: dashboard serial writes, typed identity, latest intent, decimal rejection, clamping, retry and revert while saving');
})().catch(error=>{console.error(error);process.exitCode=1;});
