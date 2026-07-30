import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import os
import time
import matplotlib.pyplot as plt


st.set_page_config(
    page_title="Recruit Searching",
    layout="centered"
)


def crawl_saramin():
    results = []

    keyword = "데이터분석"
    page = 1

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    encoded_keyword = quote(keyword)

    url = (
        "https://www.saramin.co.kr/zf_user/search/recruit"
        f"?searchType=search&searchword={encoded_keyword}&recruitPage={page}"
    )

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    job_items = soup.select("div.item_recruit")

    for item in job_items:
        company_tag = item.select_one("div.area_corp strong.corp_name a")
        title_tag = item.select_one("div.area_job h2.job_tit a")
        detail_tags = item.select("div.area_job div.job_condition span")

        company = company_tag.get_text(strip=True) if company_tag else ""
        recruit = title_tag.get_text(strip=True) if title_tag else ""

        if title_tag and title_tag.has_attr("href"):
            href = title_tag["href"]
            if href.startswith("http"):
                url_link = href
            else:
                url_link = "https://www.saramin.co.kr" + href
        else:
            url_link = ""

        detail = ", ".join([tag.get_text(strip=True) for tag in detail_tags])

        if company or recruit:
            results.append({
                "Site": "Saramin",
                "Col_Company": company,
                "Col_Recruit": recruit,
                "Col_detail": detail,
                "Col_url": url_link
            })

    df = pd.DataFrame(
        results,
        columns=["Site", "Col_Company", "Col_Recruit", "Col_detail", "Col_url"]
    )

    return df


def crawl_jobkorea():
    results = []

    keyword = "데이터분석"
    page = 1

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.jobkorea.co.kr/"
    }

    encoded_keyword = quote(keyword)

    search_url = (
        "https://www.jobkorea.co.kr/Search/"
        f"?stext={encoded_keyword}&tabType=recruit&Page_No={page}"
    )

    response = requests.get(search_url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    title_links = soup.select("a[href*='/Recruit/GI_Read/']")

    seen_links = set()

    for title_tag in title_links:
        recruit = title_tag.get_text(" ", strip=True)

        if recruit == "":
            continue

        href = title_tag.get("href", "")

        if href.startswith("http"):
            detail_url = href
        else:
            detail_url = "https://www.jobkorea.co.kr" + href

        if detail_url in seen_links:
            continue

        seen_links.add(detail_url)

        company = ""
        detail = ""

        try:
            detail_response = requests.get(detail_url, headers=headers, timeout=10)
            detail_response.raise_for_status()

            detail_soup = BeautifulSoup(detail_response.text, "html.parser")

            company_tag = detail_soup.find(
                "h2",
                class_=lambda x: x
                and "font-medium" in x
                and "text-[20px]" in x
            )

            if company_tag:
                company = company_tag.get_text(" ", strip=True)

            if company == "":
                h2_tags = detail_soup.find_all("h2")

                for tag in h2_tags:
                    text = tag.get_text(" ", strip=True)

                    if (
                        text != ""
                        and text != recruit
                        and "회원가입" not in text
                        and "로그인" not in text
                        and len(text) <= 50
                    ):
                        company = text
                        break

            full_text = detail_soup.get_text(" ", strip=True)

            region = ""

            region_keywords = [
                "서울", "경기", "인천", "부산", "대구", "대전", "광주", "울산",
                "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"
            ]

            if "근무지주소" in full_text:
                region_part = full_text.split("근무지주소", 1)[1]
                words = region_part.split()

                if len(words) >= 2:
                    region = words[0] + " " + words[1]
                elif len(words) >= 1:
                    region = words[0]

            if region == "" and "근무지역" in full_text:
                region_part = full_text.split("근무지역", 1)[1]
                words = region_part.split()

                if len(words) >= 2:
                    region = words[0] + " " + words[1]
                elif len(words) >= 1:
                    region = words[0]

            if region == "":
                for word in region_keywords:
                    if word in full_text:
                        region = word
                        break

            career = ""

            if "경력무관" in full_text:
                career = "경력무관"
            elif "신입" in full_text and "경력" in full_text:
                career = "신입·경력"
            elif "신입" in full_text:
                career = "신입"
            elif "경력" in full_text:
                career = "경력"

            education = ""

            education_keywords = [
                "학력무관",
                "고졸↑",
                "초대졸↑",
                "대졸↑",
                "석사↑",
                "박사↑",
                "고졸",
                "초대졸",
                "대졸",
                "석사",
                "박사"
            ]

            for word in education_keywords:
                if word in full_text:
                    education = word
                    break

            employment = ""

            employment_keywords = [
                "정규직",
                "계약직",
                "프리랜서",
                "인턴",
                "아르바이트",
                "파견직",
                "위촉직",
                "교육생"
            ]

            for word in employment_keywords:
                if word in full_text:
                    employment = word
                    break

            detail_items = []

            if region != "":
                detail_items.append(region)

            if career != "":
                detail_items.append(career)

            if education != "":
                detail_items.append(education)

            if employment != "":
                detail_items.append(employment)

            detail = ", ".join(detail_items)

        except Exception:
            company = ""
            detail = ""

        results.append({
            "Site": "Job_Korea",
            "Col_Company": company,
            "Col_Recruit": recruit,
            "Col_detail": detail,
            "Col_url": detail_url
        })

        time.sleep(0.5)

    df = pd.DataFrame(
        results,
        columns=["Site", "Col_Company", "Col_Recruit", "Col_detail", "Col_url"]
    )

    return df


st.title("Title")

if st.button("Recruit Searching"):

    with st.spinner("채용공고 정보를 수집하는 중입니다."):

        try:
            df_jobkorea = crawl_jobkorea()
        except Exception as e:
            st.error("Jobkorea 크롤링 중 오류가 발생했습니다.")
            st.exception(e)
            df_jobkorea = pd.DataFrame(
                columns=["Site", "Col_Company", "Col_Recruit", "Col_detail", "Col_url"]
            )

        time.sleep(1)

        try:
            df_saramin = crawl_saramin()
        except Exception as e:
            st.error("Saramin 크롤링 중 오류가 발생했습니다.")
            st.exception(e)
            df_saramin = pd.DataFrame(
                columns=["Site", "Col_Company", "Col_Recruit", "Col_detail", "Col_url"]
            )

        df_total = pd.concat(
            [df_jobkorea, df_saramin],
            ignore_index=True
        )

        df_total = df_total[
            ["Site", "Col_Company", "Col_Recruit", "Col_detail", "Col_url"]
        ]

        os.makedirs("data_tmp", exist_ok=True)

        df_jobkorea.to_csv(
            "data_tmp/data_jobkorea.csv",
            index=False,
            encoding="utf-8-sig"
        )

        df_saramin.to_csv(
            "data_tmp/data_saramin.csv",
            index=False,
            encoding="utf-8-sig"
        )

    if df_total.empty:
        st.warning("수집된 데이터가 없습니다.")
    else:
        st.dataframe(df_total)

        count_df = df_total["Site"].value_counts().reset_index()
        count_df.columns = ["Site", "Count"]

        total_count = count_df["Count"].sum()
        count_df["Ratio"] = round(count_df["Count"] / total_count * 100, 2)

        st.dataframe(count_df)

        st.write("Recruitment Ratio")

        fig, ax = plt.subplots(figsize=(8, 5))

        colors = ["#0078D7", "#7EC8F8"]

        wedges, texts, autotexts = ax.pie(
            count_df["Count"],
            autopct="%.1f%%",
            startangle=90,
            colors=colors
        )

        ax.axis("equal")

        ax.legend(
            wedges,
            count_df["Site"],
            loc="upper left",
            bbox_to_anchor=(1.05, 0.95)
        )

        st.pyplot(fig)