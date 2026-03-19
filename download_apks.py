#!/usr/bin/env python3
"""Download APKs from URLs in parallel."""
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

URLS = [
    "https://whitelabel-cdn-prod.digitalturbine.com/files/e4b13977-7997-4ab4-ba07-446d08022a44.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/aab92184-a015-48f9-88bf-3d9e0b4ba9cd.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/ba2ea026-2b75-4c7a-854c-51ba92dbfdb8.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/fd9edef6-2b91-47f0-8bb1-99c08c7e6df7.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/45cf4301-7fca-43d1-bb02-0adf5d19d4ca.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/3960c1ca-2df4-4d03-8fc5-15baac45249c.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/e840dbf1-8d42-4f99-9d00-fd0d7c59d198.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/c43adc80-e620-4941-b71e-19260ad12186.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/31ea92d2-5177-4ff0-8173-749971eea437.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/cddfc1f7-4983-4861-9e35-77bde550f929.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/ae0337a0-6be7-4189-95b9-8c749f72f3f9.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/3cb591c2-74ae-4b76-930e-89813ef1bb18.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/878bb722-f7cf-4c87-82fa-9e2afa23d0a7.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/ca01cc67-9263-480f-a564-8fb475df6286.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/6d546c33-36f8-4b84-85ba-2b7b3ca0755b.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/ac568f8d-a4d7-475f-806a-27e45ea94661.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/e090ef4a-7c80-44f7-8c87-5ed6e08602df.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/1a10d199-12d0-4ec9-a630-563197cc13a9.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/3d099418-a4c0-45ce-8015-ebc1c7fd1584.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/aac3f179-8f47-4d20-b6de-93cfa5a67bca.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/cbdf7c8b-4a9f-4794-9638-7b73433c5c29.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/83c5a841-e53b-4c1c-9f3e-e23e826c2185.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/ee1d1ee1-f06e-4e9d-af38-a387b6bb2989.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/240c60cd-4289-4f15-8d4b-b8fd482251da.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/ae16f360-a693-4d62-8d29-679fffb3ad4f.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/28119262-5966-439a-b9fa-a77f9d6b7e0c.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/da4fe19a-224a-44d6-bf98-3f1e3305605e.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/e54e140b-c037-40d9-a19d-58cbb5ba27ee.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/6fe0b007-e032-470d-b1be-09d206be1088.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/e6756338-f99f-4ea3-8b86-a6409d2eed08.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/e87a6360-a74d-431e-a059-d278ddcc86f2.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/2ee700ce-d17f-487d-b0a9-2371fe768d9f.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/b13b9ebe-54ba-433d-8f13-256177158136.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/68de793e-e659-4bdc-83fb-9c0a3aecfad7.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/46946d04-73ea-40f3-97b6-a230bc5a5d78.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/681cd269-4f33-418a-9d6f-11b3431617f0.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/d636c98d-94cf-47ae-b816-82f561e92a43.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/f49ccb7e-b682-45c1-ad9c-fe1307a315f1.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/135634e4-a4d6-470e-b351-121c061e1947.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/0cf4d867-1888-4740-8f7d-8865794333c4.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/0b77c51b-6811-4df6-a6e7-c599a2b4e15f.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/4f0b16b2-bc5b-4eba-bb0a-ef5604af5f96.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/f490c065-469b-4db3-8ecd-942fb10874d4.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/4fd2f64f-7de8-4643-9cb5-de08a4b4df3b.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/b5b383b5-f19d-43d9-bba9-21bc9d10810c.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/a0651a56-05cd-4999-bb0f-49e6ede8138b.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/09e233df-dfd3-41e3-a553-deb28584cc67.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/42ecb325-efee-45dc-ba94-2cdde0119769.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/91071faf-5fee-42b9-86de-dd21c01e65df.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/0e05d1fc-9e6a-485e-976e-8e25a888c47a.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/021dda5e-4b22-49e5-9dc7-de4473638995.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/6e9e197e-9e83-4bed-967e-651aec7543ab.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/06c8a82f-2fd7-4bf8-b7b3-95520967561b.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/2b961683-b15b-40cb-a2cf-4c8a3fb93d87.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/05ea7579-6478-4de3-aacb-5c9a46186dae.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/444cd206-f5cc-49fc-9cd3-1e7d018ab438.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/898f1591-39a7-4c36-b674-e7f06ae4e923.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/870a3f47-9cdd-44d1-94b2-fade238e3bd6.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/863ecc3d-651f-458e-9e4d-cfb384244d8d.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/84b8f945-32d9-4454-b48e-b9a675a873ed.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/bb044ffe-bb99-40e6-a506-8483fd4e9b4b.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/d60d1c1d-a1c6-40f6-8209-2c779562ddde.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/a5651b3f-afe3-40df-9e67-49edf9e84466.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/7710708c-c925-4613-b59a-a5576534bd48.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/2d31fe01-8032-4a05-80e3-b3b055d5acb9.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/74ed962f-a4cd-4501-be75-7bedb61963d9.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/0d2de3b3-17dd-43de-ab3e-eee495a649a0.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/165f88ce-892d-4e31-b5db-e5807452d5b0.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/50c27353-b406-40fe-b678-291688bb5d31.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/34f7c188-82b1-4012-bc27-93023b8bb5e2.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/32f8641d-3f8e-4f92-b982-17ac1296fae0.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/099239dc-9aa1-414a-8e36-ca27f8b7f3d0.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/60b77d0f-3964-423c-963c-fb2fdcb3453e.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/46bcf92d-da1f-487a-b29b-9b88c53fd052.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/5cc58206-94c3-496a-978a-1ac03e5e4cde.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/c8951289-1074-4a64-9bda-20304b90bf40.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/513c6d42-fa76-411d-a302-d9c7cdf00785.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/3fc1f1b7-2a13-46c4-ad5c-6ddc377c638b.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/82d0bb3f-75a7-48fb-80b5-c3b5355f7566.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/e57b2ba4-03cc-4596-be75-cd910889939f.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/25d2165f-641a-4001-bb4a-9513a6a9d67f.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/45444325-20c3-40e1-86fa-b8f9af3b27aa.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/c9e2c0ce-d77d-4414-ac9c-34ab72db3ad9.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/f3028d53-e5f9-4852-ab46-fb3865a263a9.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/2b78b0e7-12df-42fb-8b53-0cb41cba30ff.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/999568d4-074a-410e-957d-1275bf1123ba.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/6225b20b-f5c4-4826-baa1-280130670e55.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/454bed11-acfc-4a3d-b702-07f739cfc353.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/42bbee74-fb37-464d-a20e-d287cd16da0b.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/8da6d184-fba7-413a-90b3-70710a25ee34.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/07c5223d-6036-4aa2-9756-885d933bf3b9.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/73d81777-c744-46be-ab47-5d97c06efa06.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/af05ab4a-042c-40e8-8969-b39f0e0166d6.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/854ee11c-e4af-47f5-8c01-9c9af1e65743.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/217908fc-a6be-4bd9-ae2a-60e1be1c5311.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/1859cae0-bf67-4ad2-88d1-de4b7c571e13.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/c603d878-d59a-4d4c-94c6-ac40ff214853.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/963e292d-63f5-40b8-8e52-18559087f52f.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/61965b5a-fd8b-4345-8b35-b606380023b9.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/32c5c004-e7ab-4bc9-89bc-b2a42739ee70.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/781d2dac-7b14-4b51-ab02-f2f56dc34082.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/25aea97d-0a80-40a1-9800-c2eb40e4da50.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/6f951183-10ed-4f05-9506-5c310aa0f15c.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/e6fcab1f-715b-4501-839b-c925f8aaf8b4.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/783cea60-cbee-4150-b9e6-20266ad7d8ee.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/7af08e4d-73c3-4862-abc7-2d55cb4134a3.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/d9aea0d4-874d-4dff-97e6-0e0b499710d7.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/51eb5505-ab68-44c4-96ce-7d1cd1696e7a.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/0de9b2d6-4b7b-47d2-b831-55cf90e592ba.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/f776cf54-0ad9-4182-af0d-27fcd368066f.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/252df8e5-bc05-4e25-b5f4-12216e2715bb.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/964b6f56-36b4-4e9a-b82e-367a5f06db23.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/bb58ed80-4780-433d-bfa6-49badbf3948d.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/887e4956-cd18-48c7-b4f9-106fda2d8850.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/4e0a8e12-bfea-4e22-96ae-c797bfa55587.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/a86e2677-b218-4e4c-a4ce-bf7d1b25e770.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/475a0e1f-9739-401c-bba7-f263e9ce6d18.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/a9bbd758-dacf-4cc8-9194-2e714357b351.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/53d126cd-5f9d-4f2d-aef8-53e37ea9846b.apk",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/d7e4c37b-e0b2-40eb-b2da-69f239ba688c.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/72510107-af06-49a0-bf9a-a3093c34bd67.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/dedfd8c0-33af-4bd7-ac2b-27614dd1dfda.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/63774e06-45ad-4df9-b482-5c1969566a96.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/cdcedd2c-0efa-4361-9048-3f0b6d96fc45.apks",
    "https://whitelabel-cdn-prod.digitalturbine.com/files/17c45bb8-2a35-46d1-ae53-9eb44fd81221.apks",
]

OUTPUT_DIR = "/workspace/apks"

def download_file(url, retries=3):
    """Download a file from URL with retries."""
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    output_path = os.path.join(OUTPUT_DIR, filename)
    
    if os.path.exists(output_path):
        return f"[SKIP] {filename} already exists"
    
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=120) as response:
                with open(output_path, 'wb') as out_file:
                    out_file.write(response.read())
            return f"[OK] {filename}"
        except Exception as e:
            if attempt == retries - 1:
                return f"[FAIL] {filename}: {e}"
    return f"[FAIL] {filename}: unknown error"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"Downloading {len(URLS)} files to {OUTPUT_DIR}...")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(download_file, url): url for url in URLS}
        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            print(f"[{completed}/{len(URLS)}] {result}")
    
    # List downloaded files
    files = os.listdir(OUTPUT_DIR)
    apk_files = [f for f in files if f.endswith('.apk')]
    apks_files = [f for f in files if f.endswith('.apks')]
    
    print(f"\n=== Download Complete ===")
    print(f"APK files: {len(apk_files)}")
    print(f"APKS files: {len(apks_files)}")
    print(f"Total: {len(apk_files) + len(apks_files)}")

if __name__ == "__main__":
    main()
