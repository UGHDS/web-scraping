const puppeteer = require("puppeteer");
const fs = require("fs");

(async () => {
    let data = {};
    let count = 3;//限制10个ASIN
    const ASINs = new Set();  // 用于存储ASINs的集合
    const visitedASINs = new Set();  // 用于存储已访问的ASINs

    const browser = await puppeteer.launch({
        headless:false,
        userDataDir: "./data",
        args: ['--lang=en-US,en']
    });

    const page = await browser.newPage();

    //起始页码
    const startUrl = "https://www.amazon.com/dp/B01LYOCVZF";

    const startASIN = extractASINFromURL(startUrl);
    ASINs.add(startASIN);

    while (ASINs.size && count > 0) {
        const currentASIN = ASINs.values().next().value;  // 取出一个ASIN
        ASINs.delete(currentASIN);  // 从待访问集合中移除
        visitedASINs.add(currentASIN);  // 添加到已访问集合
        count--;

        // 组合出商品信息URL 和其对应评论页URL
        const currentUrl = `https://www.amazon.com/dp/${currentASIN}`;
        const currentReviewsUrl = `https://www.amazon.com/product-reviews/${currentASIN}/`;
        await page.goto(currentUrl);

        // 从页面所有URL中，提取页面上的所有ASINs
        const links = await page.$$eval("a", anchors => anchors.map(a => a.href));
        for (const link of links) {
            const ASIN = extractASINFromURL(link);
            if (ASIN && !visitedASINs.has(ASIN)) { // 如果未添加过ASIN
                ASINs.add(ASIN);
            }
        }

        console.log([...visitedASINs]);  // 输出所有提取到的ASINs

        // 获取商品信息
        // 获取商品评论页的前五页上所有评论
        for (let pg = 1; pg < 5; pg++) {
            await page.goto(
                currentReviewsUrl +
                `ref=cm_cr_arp_d_paging_btm_next_${pg}?ie=UTF8&reviewerType=all_reviews&pageNumber=${pg}`
            );

            await page.waitForSelector('div[data-cel-widget^="customer_review"]');
    
            // 使用了page.$eval方法，它只返回匹配给定选择器的第一个元素的结果。为了提取所有匹配选择器的元素，应该使用page.$$eval方法。
            const reviewData = await page.$$eval('div[data-cel-widget^="customer_review"]', (reviewElements) => {
                return reviewElements.map(reviewElement => {
                    // 提取评分
                    const ratingElement = reviewElement.querySelector('i[data-hook="review-star-rating"]');
                    const rating = ratingElement ? parseFloat(ratingElement.textContent.trim().split(' ')[0]) : null;

                    // 提取评论标题
                    const titleElement = reviewElement.querySelector('a[data-hook="review-title"]');
                    let title = titleElement ? titleElement.textContent.trim() : null;

                    if (title) {
                        // 使用split方法分割字符串，并取最后一个部分作为真正的标题
                        title = title.split('\n').pop().trim();
                    }

                    // 提取评论内容
                    const bodyElement = reviewElement.querySelector('span[data-hook="review-body"]');
                    const body = bodyElement ? bodyElement.textContent.trim() : null;

                    // 提取评论人名称
                    const nameElement = reviewElement.querySelector('span.a-profile-name');
                    const name = nameElement ? nameElement.textContent.trim() : null;

                    // 提取评论时间
                    const dateElement = reviewElement.querySelector('span[data-hook="review-date"]');
                    const date = dateElement ? dateElement.textContent.replace('Reviewed in the United States on', '').trim() : null;

                    return {
                        rating,
                        title,
                        body,
                        name,
                        date
                    };
                });
            });

            console.log(reviewData);

            // console.log(reviews);
            // data = data.concat(reviews);

            // 如果data中还没有该ASIN的条目，则创建一个
            if (!data[currentASIN]) {
                data[currentASIN] = {
                    reviews: [],
                    // 为后续扩展预留字段
                    // name: "",
                    // price: 0,
                    // stock: 0,
                    // ...
                };
                // data[currentASIN].reviews.push(reviewData);
            }
            // }else{
            //     // 当使用 concat 方法时，它会返回一个新的数组，而不是修改原始数组。所以，需要将返回的新数组重新赋值给原始数组。
            //     data[currentASIN].reviews = data[currentASIN].reviews.concat(reviewData);
            // }

            // 当使用 concat 方法时，它会返回一个新的数组，而不是修改原始数组。所以，需要将返回的新数组重新赋值给原始数组。
            data[currentASIN].reviews = data[currentASIN].reviews.concat(reviewData);
            
        }
    }

    // 将所有已访问的ASINs写入文件
    fs.writeFile("ASINs.json", JSON.stringify([...visitedASINs], null, "\t"), function (err) {
        if (err) {
            console.log(err);
        }
    });

    fs.writeFile("data.json", JSON.stringify(data, null, "\t"), function (err) {
        if (err){
            console.log(err);
        }
    });

    await browser.close();

    // 从URL中提取ASIN的函数
    function extractASINFromURL(url) {
        const match = url.match(/\/dp\/([A-Z0-9]{10})/);
        return match ? match[1] : null;
    }
})();