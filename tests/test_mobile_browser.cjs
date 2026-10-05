// Optional browser smoke test; see docs/SIGNUP_AND_MOBILE.md for setup.
const { chromium: playwright } = require('playwright-core');
const fs = require('node:fs');
(async () => {
 const browser = await playwright.launch({ executablePath: process.env.CHROMIUM_EXECUTABLE_PATH || undefined, args: ['--no-sandbox'], headless: true });
 const page = await browser.newPage({viewport:{width:375,height:667},isMobile:true,deviceScaleFactor:1,hasTouch:true});
 const errors=[]; page.on('pageerror',e=>errors.push(e.message));
 const signups=[];
 await page.route('**/*', async route => {
  const url=new URL(route.request().url());
  if(url.pathname==='/login') return route.fulfill({contentType:'text/html',body:fs.readFileSync('static/index.html')});
  if(url.pathname.startsWith('/static/')) {
   const name=url.pathname.slice(1);
   return route.fulfill({contentType:name.endsWith('.css')?'text/css':'text/javascript',body:fs.readFileSync(name)});
  }
  if(url.pathname==='/api/auth/signup') {
   signups.push(route.request().postDataJSON());
   return route.fulfill({status:409,json:{detail:'Email already registered'}});
  }
  if(url.pathname==='/api/auth/me') return route.fulfill({status:401,json:{detail:'Not authenticated'}});
  return route.fulfill({json:[]});
 });
 await page.goto('https://parlez.test/login');
 await page.locator('#authToggleLink').click();
 await page.locator('#authEmail').fill('bad-email');
 if(await page.locator('#authEmail').evaluate(el=>el.checkValidity())) throw Error('Email field accepted invalid address');
 await page.locator('#authUsername').fill('learner');
 await page.locator('#authPassword').fill('password123');
 await page.locator('#authSubmit').click();
 if(signups.length) throw Error('Invalid email reached signup endpoint');
 await page.locator('#authEmail').fill('learner@example.com');
 await page.locator('#authSubmit').click();
 await page.locator('#authError').waitFor({state:'visible'});
 if(signups[0]?.email!=='learner@example.com') throw Error('Signup payload missing email');
 if(await page.locator('#authSubmit').isDisabled()) throw Error('Submit left disabled');
 await page.locator('#authToggleLink').click();
 if(!await page.locator('#authEmail').isDisabled()) throw Error('Login email not disabled');
 await page.evaluate(()=>showApp());
 for(const [width,height] of [[320,568],[375,667],[390,844],[667,375],[375,350],[1280,800]]) {
  await page.setViewportSize({width,height});
  await page.evaluate(()=>{ document.getElementById('messages').innerHTML=Array.from({length:30},()=>'<div class="message"><div class="message-bubble">Bonjour — a long conversation message.</div></div>').join(''); });
  await page.locator('#messageInput').fill('Bonjour');
  await page.waitForTimeout(100);
  const box=await page.locator('#messageInput').boundingBox();
  const send=await page.locator('#sendButton').boundingBox();
  const metrics=await page.evaluate(()=>({height:visualViewport.height,width:visualViewport.width,scroll:document.documentElement.scrollWidth}));
  console.log(width,height,box,metrics);
  if(!box||box.width<100||box.y+box.height>metrics.height+1||box.x<0||send.x+send.width>metrics.width+1) throw Error('Composer outside viewport');
 }
 if(errors.length) throw Error(errors.join('\n'));
 await browser.close();
 console.log('Mobile browser and auth UI checks passed');
})().catch(e=>{console.error(e);process.exit(1)});
