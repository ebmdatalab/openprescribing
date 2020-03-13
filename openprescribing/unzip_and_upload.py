import datetime
import os
import glob
from gcutils.storage import Client

client = Client()
bucket = client.get_bucket()

for zip_filename in sorted(glob.glob("*.zip")):
    print(datetime.datetime.now())
    assert len(zip_filename) == len("DPI_DETAIL_PRESCRIBING_YYYYMM.zip")
    assert zip_filename[:23] == "DPI_DETAIL_PRESCRIBING_"
    assert zip_filename[-4:] == ".zip"

    csv_filename = zip_filename[:-4] + ".csv"

    year_and_month = zip_filename[23:-6] + "_" + zip_filename[-6:-4]
    location = "hscic/prescribing_v2/{}/{}".format(year_and_month, csv_filename)

    blob = bucket.blob(location)

    if blob.exists():
        print("Skipping {}, already uploaded".format(csv_filename))
        continue

    if not os.path.exists(csv_filename):
        print("Unzipping {}".format(zip_filename))
        os.system("unzip {}".format(zip_filename))
    else:
        print("Already unzipped {}".format(zip_filename))

    print("Uploading {} to {}".format(csv_filename, location))
    with open(csv_filename, "rb") as f:
        blob.upload_from_file(f)

    os.unlink(csv_filename)
