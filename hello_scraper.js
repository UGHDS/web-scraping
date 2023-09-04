const puppeteer = require("puppeteer");
const fs = require("fs");

(async () => {
    let data = [];

    const visitedUrls = new Set();
    const browser = await puppeteer.launch({
        headless:false,
        userDataDir: "./data",
    });
    const page = await browser.newPage();
    const startUrl = "https://www.amazon.com/Just-Dance-2023-Code-Nintendo-Switch/product-reviews/B0BDWYGB4K/";
    visitedUrls.add(startUrl);
    const urlsToVisit = [startUrl];

    while (urlsToVisit.length) {
        const currentUrl = urlsToVisit.pop();
        for (let pg = 1; pg < 5; pg++) {
            await page.goto(
                currentUrl +
                `ref=cm_cr_arp_d_paging_btm_next_${pg}?ie=UTF8&reviewerType=all_reviews&pageNumber=${pg}`
            );
        
            await page.waitForSelector("div.a-row.a-spacing-small.review-data > span > span");
            let reviews = await page.$$eval(
                "div.a-row.a-spacing-small.review-data > span > span",
                (links) => links.map((x) => x.innerText)
            );
            console.log(reviews);
            data = data.concat(reviews);

            // Extract links from the current page
            await page.waitForSelector("#CardInstance-Y8XnKkXUpz2Ksu2Cq8xCw > div > div:nth-child(2) > div > div.a-row.a-carousel-controls.a-carousel-row.a-carousel-has-buttons");
            const links = await page.$$eval("#CardInstance-Y8XnKkXUpz2Ksu2Cq8xCw > div > div:nth-child(2) > div > div.a-row.a-carousel-controls.a-carousel-row.a-carousel-has-buttons", (anchors) => 
            anchors.map((a) => a.href)
            .filter(href => href && href.includes('amazon.com'))
            .map(href => {
                // 使用正则表达式匹配基础URL和产品ID
                // const match = href.match(/\/([^\/]+)\/dp\/([^\/]+)\//);
                // if (match) {
                //     const baseURL = match[1];
                //     const productId = match[2];
                //     // 拼接新的URL
                //     return `${baseURL}/product-reviews/${productId}/`;
                // }
                return href;  // 如果不匹配，返回null
            })
            .filter(href => href !== null)  // 过滤掉null值
            );
            // 确保页面上的元素已加载
            await page.waitForSelector("#rhf-shoveler");

            // 从指定选择器下提取所有链接
            // const links = await page.$$eval("#rhf-shoveler", anchors => anchors.map(a => a.href));

            console.log(links);  // 输出处理后的链接列表

            for (const link of links) {
                try {
                    await page.goto(link);
            
                    // 设置超时时间为10秒
                    await page.waitForSelector("div.a-row.a-spacing-small.review-data > span > span", { timeout: 10000 });
            
                    let reviews = await page.$$eval(
                        "div.a-row.a-spacing-small.review-data > span > span.cr-original-review-content",
                        (links) => links.map((x) => x.innerText)
                    );
                    console.log(reviews);
                    data = data.concat(reviews);
                } catch (error) {
                    console.error(`Error on page ${link}: ${error.message}`);
                }
            }
        }
    }

    fs.writeFile("data.json", JSON.stringify(data, null, "\t"), function (err) {
        if (err){
            console.log(err);
        }
    });

    await browser.close();
})();