import asyncio
import json
import re

import pyppeteer
from pyppeteer import launch
import time
from datetime import datetime
import math
from pyppeteer.errors import NetworkError

async def main():
    start_time = time.time()
    data = {}
    count = 1  # 限制10个ASIN
    asins = set()  # 用于存储ASINs的集合
    visited_asins = set()  # 用于存储已访问的ASINs

    browser = await launch(
        headless=False,
        userDataDir='./data',
        args=['--lang=en-US,en']
    )

    page = await browser.newPage()
    # await page.setRequestInterception(True)
    # page.on("request", lambda req: asyncio.ensure_future(intercept_request(req)))

    # page_num = count//24 + 2
    page_num = 200

    for pages in range(1, page_num):
        if count == 0:
            break

        #  起始页码
        startUrl = f"https://www.amazon.com.au/s?k=Laptops&i=computers&rh=n%3A4913311051&page={pages}&ref=sr_pg_{pages}"
        # await page.goto(startUrl)
        #
        # # 从页面所有URL中，提取页面上的所有ASINs
        # links = await page.querySelectorAllEval('a', 'anchors => anchors.map(a => a.href)')
        # for link in links:
        #     asin = extract_asin_from_url(link)
        #     # 如果未添加过ASIN
        #     if asin and asin not in visited_asins:
        #         asins.add(asin)

        try:
            await page.goto(startUrl, timeout=20000)  # Increase timeout to 20 seconds

            # Wait for at least one link to be visible on the page
            await page.waitForSelector('a', timeout=5000)

            links = await page.querySelectorAllEval('a', 'anchors => anchors.map(a => a.href)')
            for link in links:
                asin = extract_asin_from_url(link)
                if asin and asin not in visited_asins:
                    asins.add(asin)
        except pyppeteer.errors.TimeoutError:
            print(f"Timeout error on page {pages}. Skipping...")
        except Exception as e:
            print(f"An error occurred on page {pages}: {e}. Skipping...")

        while asins and count > 0:
            current_asin = asins.pop()  # 取出一个ASIN, 从待访问集合中移除
            visited_asins.add(current_asin)  # 添加到已访问集合
            count -= 1
            if(count == 10):
                continue

            # 组合出商品信息URL 和其对应评论页URL
            # current_url = f"https://www.amazon.com.au/dp/{current_asin}"
            # current_reviews_url = f"https://www.amazon.com.au/product-reviews/{current_asin}/"
            current_url = f"https://www.amazon.com.au/dp/B0C7852R89"
            current_reviews_url = f"https://www.amazon.com.au/product-reviews/B0C7852R89/"
            await page.goto(current_url)

            print(list(visited_asins))  # 输出所有提取到的ASINs

            # 获取商品信息
            total_ratings = 0
            rating_value = 0.0
            star_rating_number = {}
            review_rating = 0
            review_info = None
            image_url = None
            product_name = None
            product_price = None
            item_model_number = None

            Brand = None
            Model_name = None
            Screen_size = None
            Colour= None
            Hard_disk_size = None
            CPU_model = None
            RAM_memory_installed_size = None
            Operating_system = None

            # 获取图片url
            try:
                await page.waitForSelector('#landingImage', timeout=5000)
                image_url = await page.querySelectorEval(
                    '#landingImage',
                    'el => el.src')
            except asyncio.TimeoutError:
                print('image_url not found.')
                image_url = ''
            print(f'Image Url: {image_url}')  # 打印提取的图片url

            # 获取product name
            try:
                await page.waitForSelector('#productTitle', timeout=5000)
                product_name_content = await page.querySelectorEval(
                    '#productTitle',
                    'el => el.textContent') # 使用选择器获取元素的内容
            except asyncio.TimeoutError:
                print('product_name not found.')
                product_name_content = ''
            # product_name = product_name_content.strip().split(',')[0]  # 去除空格并按照逗号切分，获取第一部分
            # product_name = product_name_content.strip().replace('\u00a0', ' ').replace('\u2011', '-').replace('', '')  # 去除空格
            product_name = re.sub(r'[\u2000-\u200f\u2028-\u202f\u205f-\u206f\uFEFF]', '', product_name_content).strip().replace("&ZeroWidthSpace;", "") # 置换为空字符串，防止多个连续空格出现
            print(f'Product Name: {product_name}')  # 打印提取的title

            # 获取product price
            try:
                await page.waitForSelector('span[class="a-offscreen"]', timeout=5000)
                product_price_content = await page.querySelectorEval(
                    'span[class="a-offscreen"]',
                    'el => el.textContent')  # 使用选择器获取元素的内容
            except asyncio.TimeoutError:
                print('product_name not found.')
                product_price_content = ''


            # product_price = float(product_price_content.strip().replace(',', '').split('$')[1])  # 去除空格并按照$切分，获取第二部分,注意去除逗号，1,617.00
            match = re.search(r"\$([\d,]+(\.\d{2})?)", product_price_content)
            if match:
                product_price_str = match.group(1).replace(',', '')  # 获取匹配的数字部分并删除逗号
                product_price = float(product_price_str)
            else:
                product_price = None
            print(f'Product Price: {product_price}')  # 打印提取的price

            # 为了获取"Item Model Number"的值，我们需要定位到包含这个文本的th元素，然后定位到其相邻的td元素
            # 首先，获取所有<th>元素
            ths = await page.JJ('th.a-color-secondary.a-size-base.prodDetSectionEntry')

            # 初始化item_model_number
            item_model_number_raw = None

            # 循环遍历每个<th>元素，并检查其文本内容
            for th in ths:
                th_text = await page.evaluate('(element) => element.textContent', th)
                if "Item Model Number" in th_text.strip():
                    # 找到了正确的<th>元素。现在，获取其旁边的<td>元素的文本内容
                    td = await th.xpath('following-sibling::td[1]')
                    if td:  # 确保有<td>元素
                        item_model_number_raw = await page.evaluate('(element) => element.textContent', td[0])
                        item_model_number = item_model_number_raw.replace('\u200e', '').strip()    # 除去/u200e, "Left-to-Right Mark"（LTR Mark）。它是一个不可见的字符，通常用于控制文本的方向。
                        break

            print(f'Item Model Number: {item_model_number}')  # 打印提取的Item Model Number

            details = await get_table_details(page)

            Brand = details.get("Brand")
            if item_model_number is None:
                item_model_number = details.get("Model name")

            Screen_size_raw = details.get("Screen size")
            if Screen_size_raw != "":
                match = re.search(r"(\d+(\.\d+)?)", Screen_size_raw)
                if match:
                    Screen_size = float(match.group(1))  # 使用正则表达式从字符串中提取数字
                else:
                    Screen_size = None
            else:
                Screen_size = ""
                # Screen size
                screen_match = re.search(r'(\d+)″ Retina Display', product_name)
                if screen_match:
                    Screen_size = float(screen_match.group(1))
                    print("Screen size:", Screen_size)
                else:
                    Screen_size = None

            Colour = details.get("Colour")
            Hard_disk_size = details.get("Hard disk size")
            CPU_model = details.get("CPU model")

            RAM_memory_installed_size_raw = details.get("RAM memory installed size")
            if RAM_memory_installed_size_raw is not None:
                match = re.search(r"(\d+)", RAM_memory_installed_size_raw)
                if match:
                    RAM_memory_installed_size = int(match.group(1))  # 使用正则表达式从字符串中提取数字
                else:
                    RAM_memory_installed_size = None
            else:
                RAM_memory_installed_size = RAM_memory_installed_size_raw

            Operating_system = details.get("Operating system")

            if Hard_disk_size == "":
                # Extract total storage
                storage_match = re.search(r'(\d+GB) SSD Storage', product_name)
                if storage_match:
                    Hard_disk_size = storage_match.group(1)
                    print(f"Total storage: {Hard_disk_size}")

            if CPU_model == "":
                # Extract CPU model
                cpu_match = re.search(r'Apple (\w+ Chip)', product_name)
                if cpu_match:
                    CPU_model = cpu_match.group(1)
                    print(f"CPU Model: {CPU_model}")

            print(details)

            true_pg = 6

            # 获取商品评论页的前五页上所有评论
            for pg in range(1, true_pg):
                review_page_url = f"{current_reviews_url}ref=cm_cr_arp_d_paging_btm_next_{pg}?ie=UTF8&reviewerType=all_reviews&pageNumber={pg}"
                await page.goto(review_page_url)

                if pg == 1:
                    # 评分信息
                    # review_info = await page.querySelectorEval('div[data-hook="cr-filter-info-review-rating-count"]',
                    #                                            lambda el: el.textContent.strip())
                    try:
                        await page.waitForSelector('div[data-hook="cr-filter-info-review-rating-count"]', timeout=5000)
                        review_info = await page.querySelectorEval(
                            'div[data-hook="cr-filter-info-review-rating-count"]',
                            'el => el.textContent.trim()')  # 获取文本内容并去掉两端的空白字符
                    except asyncio.TimeoutError:
                        print('Element not found.')
                        review_info = ''

                    # 使用正则表达式提取数字,数字有可能是“3,003”
                    # match_review_info = re.search(r'([\d,]+) total ratings, ([\d,]+) with reviews', review_info)
                    # match_review_info = re.search(r'([\d,]+) total ratings, ([\d,]+) with review(s)?', review_info)

                    # if match_review_info:
                    #     total_ratings = int(match_review_info.group(1).replace(',', ''))  # 删除逗号，然后转换为整数
                    #     total_reviews = int(match_review_info.group(2).replace(',', ''))  # 删除逗号，然后转换为整数
                    #
                    #     true_pg = math.ceil(total_reviews/10) + 1
                    #     print(f'Total Ratings: {total_ratings}, Total Reviews: {total_reviews}')
                    # else:
                    #     true_pg = 1
                    #     print('Unable to extract review numbers.')

                    # 使用非贪婪的匹配，并为第二个数字设置一个可选的匹配
                    match_review_info = re.search(r'([\d,]+) total rating(?:s)?(?:, ([\d,]+) with review(?:s)?)?', review_info)

                    if match_review_info:
                        total_ratings = int(match_review_info.group(1).replace(',', ''))  # 删除逗号，然后转换为整数

                        # 如果匹配到第二个数字，提取它，否则默认为total_ratings
                        total_reviews = int(match_review_info.group(2).replace(',', '')) if match_review_info.group(2) else 0

                        true_pg = math.ceil(total_reviews / 10) + 1
                        print(f'Total Ratings: {total_ratings}, Total Reviews: {total_reviews}')
                    else:
                        true_pg = 1
                        print('Unable to extract review numbers.')


                    try:
                        await page.waitForSelector('span[data-hook="rating-out-of-text"]', timeout=5000)
                        review_rating = await page.querySelectorEval(
                            'span[data-hook="rating-out-of-text"]',
                            'el => el.textContent.trim()')  # 获取文本内容并去掉两端的空白字符
                    except asyncio.TimeoutError:
                        print('Element not found.')
                        review_rating = ''

                    # review_rating = await page.querySelectorEval('span[data-hook="rating-out-of-text"]',
                    #                                              lambda el: el.textContent.strip())
                    rating_value = float(review_rating.split(' ')[0])  # 使用空格将字符串分割成数组，并获取第一个元素（即评分数值）
                    print(f'Rating Value: {rating_value}')  # 打印提取的评分数值

                    # 各个星级评分数量
                    for index in range(1, 6):
                        selector = f'tr:nth-child({index}) > td.a-text-right.a-nowrap > span.a-size-base > a'
                        element = await page.querySelector(selector)  # 等待元素加载

                        if not element:
                            star_rating_number[index] = 0
                            print(f'StarRatingNumber[{index}] = 0')
                        else:
                            star_rating = await page.evaluate('(element) => element.textContent.trim()', element)
                            star_rating = star_rating.replace('%', '')
                            star_rating_number[index] = int(star_rating)
                            print(f'StarRatingNumber[{index}] = {star_rating_number[index]}')

                    print(star_rating_number)

                    # 如果data中还没有该ASIN的条目，则创建一个
                    if current_asin not in data:
                        data[current_asin] = {
                            'image_url': image_url,
                            'product_name': product_name,
                            'product_price' : product_price,
                            'item_model_number' : item_model_number,
                            'Brand' : Brand,
                            'Display size' : Screen_size,
                            'Colour' : Colour,
                            'Total storage' : Hard_disk_size,
                            'CPU Model' : CPU_model,
                            'RAM' : RAM_memory_installed_size,
                            'Operating system' : Operating_system,
                            'total_ratings': total_ratings,
                            'rating_number': rating_value,
                            'five_star_rating_number': star_rating_number[1],
                            'four_star_rating_number': star_rating_number[2],
                            'three_star_rating_number': star_rating_number[3],
                            'two_star_rating_number': star_rating_number[4],
                            'one_star_rating_number': star_rating_number[5],
                            'reviews': []
                        }

                if pg == true_pg:
                    break

                # 等待元素出现或者超时
                try:
                    await page.waitForSelector('div[data-cel-widget^="customer_review"]', timeout=5000)
                except asyncio.TimeoutError:
                    print('超时，跳过')
                    break

                review_elements = await page.querySelectorAll('div[data-cel-widget^="customer_review"]')
                review_data = []

                for review_element in review_elements:
                    review_item = {}

                    # 提取评分
                    rating_element = await review_element.querySelector('i[data-hook="review-star-rating"]') or \
                                     await review_element.querySelector('i[data-hook="cmps-review-star-rating"]')
                    if rating_element:
                        rating_text = await page.evaluate('(element) => element.textContent', rating_element)
                        review_item['rating'] = float(rating_text.strip().split(' ')[0])

                    # 提取评论标题
                    title_element = await review_element.querySelector('a[data-hook="review-title"]') or \
                                    await review_element.querySelector('span[data-hook="review-title"]')
                    if title_element:
                        title_text = await page.evaluate('(element) => element.textContent', title_element)
                        review_item['title'] = title_text.strip().split('\n').pop().strip()

                    # 提取评论内容
                    body_element = await review_element.querySelector(
                        'div.a-row.a-spacing-small.review-data > span > span')
                    if body_element:
                        body_text = await page.evaluate('(element) => element.textContent', body_element)
                        review_item['body'] = body_text.strip()

                    # 提取评论人名称
                    name_element = await review_element.querySelector('span.a-profile-name')
                    if name_element:
                        name_text = await page.evaluate('(element) => element.textContent', name_element)
                        review_item['name'] = name_text.strip()

                    # 提取评论时间
                    date_element = await review_element.querySelector('span[data-hook="review-date"]')
                    if date_element:
                        date_text = await page.evaluate('(element) => element.textContent', date_element)
                        date_text = re.sub(r'^.* on ', '', date_text).strip()

                        # 使用 datetime.strptime 解析字符串
                        date_object = datetime.strptime(date_text, "%d %B %Y")

                        # 使用 strftime 将日期对象格式化为所需格式
                        formatted_date = date_object.strftime("%Y-%m-%d")

                        # print(formatted_date)  # 输出：2023-07-19

                        review_item['date'] = formatted_date

                    review_data.append(review_item)

                print(review_data)



                data[current_asin]['reviews'].extend(review_data)

    # 写入文件
    write_to_file("asins.json", list(visited_asins))  # 将所有已访问的ASINs写入文件
    write_to_file("data.json", data)

    # 首先关闭所有页面，然后再关闭浏览器
    for page in await browser.pages():
        try:
            await page.close()
        except Exception as e:
            print(f"Error when closing a page: {e}")

    await asyncio.sleep(2)  # 在关闭浏览器之前添加一个延迟，以确保所有操作都已完成

    try:
        await browser.close()
    except NetworkError:
        print("NetworkError occurred while closing the browser.")
    except Exception as e:
        print(f"Error when closing browser: {e}")

    end_time = time.time()
    print(f"Total time taken: {end_time - start_time} s")


# 从URL中提取ASIN的函数
def extract_asin_from_url(url):
    match = re.search(r"/dp/([A-Z0-9]{10})", url)
    return match.group(1) if match else None


def write_to_file(file_name, data):
    with open(file_name, "w") as file:
        json.dump(data, file, indent="\t")


async def intercept_request(req):
    if req.resourceType in ["image", "stylesheet"]:
        await req.abort()
    else:
        await req.continue_()


# 获取商品详情
async def get_table_details(page):
    # 预定义一个字典，其中包含所有希望匹配的标签以及其默认值（为空字符串）
    labels_to_extract = {
        "Brand": "",
        "Model name": "",
        "Screen size": "",
        "Colour": "",
        "Hard disk size": "",
        "CPU model": "",
        "RAM memory installed size": "",
        "Operating system": ""
    }

    await page.evaluate('window.scrollBy(0, 1000)')  # Scroll down by 1000 pixels

    # 尝试新版本的HTML结构
    # 获取所有行
    try:
        rows = await page.JJ(".a-section.a-spacing-small > div.a-row.a-spacing-small")
    except pyppeteer.errors.TimeoutError:
        rows = []  # 如果超时，将rows设置为空列表，以便下面的if语句可以执行

    if rows: # 如果找到了行
        for row in rows:
            await page.waitForSelector("span.a-size-base.a-text-bold")
            await page.waitForSelector("span.a-size-base.po-break-word")

            label_elem = await row.querySelector("span.a-size-base.a-text-bold")
            value_elem = await row.querySelector("span.a-size-base.po-break-word")

            if label_elem and value_elem:
                # page.evaluate是一个协程（coroutine），它返回一个Future对象，而不是直接返回结果。需要用await关键字获取实际的结果。
                # label = await page.evaluate('(element) => element.textContent', label_elem).replace(":", "").strip()
                # value = await page.evaluate('(element) => element.textContent', value_elem).strip()
                label = (await page.evaluate('(element) => element.textContent', label_elem)).replace(":", "").strip()
                value = (await page.evaluate('(element) => element.textContent', value_elem)).strip()


                # 如果标签在我们的预定义字典中，则更新其值
                if label in labels_to_extract:
                    labels_to_extract[label] = value

    # 检查是否正确提取了数据，如果新版本失败，尝试原始版本的HTML结构
    if not any(value for value in labels_to_extract.values()):  # 如果所有值都是空的
        try:
            await page.waitForXPath("//table[@class='a-normal a-spacing-micro']/tbody/tr",timeout=10000)  # 解决有时rows为空，无法获得的问题
            rows = await page.xpath("//table[@class='a-normal a-spacing-micro']/tbody/tr")
            # rows = await page.xpath("//table[@class='a-normal a-spacing-micro']/tbody/tr", timeout=10000)
        except pyppeteer.errors.TimeoutError:
            rows = []  # 如果超时，将rows设置为空列表，以便下面的if语句可以执行

        for row in rows:
            label_elem = await row.querySelector(".a-span3 span")
            value_elem = await row.querySelector(".a-span9 span")

            if label_elem and value_elem:
                label = await page.evaluate('(element) => element.textContent', label_elem)
                value = await page.evaluate('(element) => element.textContent', value_elem)

                if label.strip() in labels_to_extract:
                    labels_to_extract[label.strip()] = value.strip()

    return labels_to_extract  # 如果两种方法都失败，返回默认的labels_to_extract

asyncio.get_event_loop().run_until_complete(main())
