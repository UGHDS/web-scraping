const puppeteer = require("puppeteer");
const fs = require("fs");

(async () => {
    let data = {};

    const browser = await puppeteer.launch({
        headless:false,
        userDataDir: "./data",
        args: ['--lang=en-US,en']
    });

    const page = await browser.newPage();

    //起始页码
    const startUrl = "https://www.jbhifi.com.au/products/apple-macbook-pro-13-inch-with-m2-chip-256gb-ssd-space-grey-2022";
    await page.goto(startUrl);

    await page.waitForSelector('#reviews > div.pdp-jss-accordionHead-156.accordion-head.Accordion_styles_head__iw66k72 > div.Accordion_headOpenClose__iw66k70 > svg');
    await page.click('#reviews > div.pdp-jss-accordionHead-156.accordion-head.Accordion_styles_head__iw66k72 > div.Accordion_headOpenClose__iw66k70 > svg'); // 这里的 '#buttonId' 是你要点击的按钮的 CSS 选择器
    
    await page.waitForSelector(".bv-rnr__sc-16dr7i1-3.cUMort"); // 等待评论加载
    let reviews = await page.$$eval(
        ".bv-rnr__sc-16dr7i1-3.cUMort", 
        elements => elements.map(element => element.innerText) // 使用 element 而不是 x，增加 clarity
    );

    // await page.waitForSelector("#reviews_container > div:nth-child(1) > div > div > div > div.bv-rnr__sc-16dr7i1-9.ejtslE > div.bv-rnr__sc-16dr7i1-12.lnFyiP > div > div.bv-rnr__sc-16dr7i1-3.cUMort");
    // let reviews = await page.$$eval(
    //     "#reviews_container > div:nth-child(1) > div > div > div > div.bv-rnr__sc-16dr7i1-9.ejtslE > div.bv-rnr__sc-16dr7i1-12.lnFyiP > div > div.bv-rnr__sc-16dr7i1-3.cUMort",
        
    //     (links) => links.map((x) => x.innerText)
    // );
    console.log(reviews);
    // data = data.concat(reviews);

    // fs.writeFile("data2.json", JSON.stringify(data, null, "\t"), function (err) {
    //     if (err){
    //         console.log(err);
    //     }
    // });
    // await page.waitForSelector(' div.bv-rnr__sc-11r39gb-1.kCsdrb > div > ul > li:nth-child(2) > a');
    // await page.click(' div.bv-rnr__sc-11r39gb-1.kCsdrb > div > ul > li:nth-child(2) > a');
    // await browser.close();
})();