import sys
import os
sys.path
sys.path.append(os.path.abspath('fcs_lambda'))

from lambda_function import extract_record, save_record

record=extract_record("cytovas-instrument-files","04abf37b-a1de-40c0-86c6-2353f7b15c91.fcs")

print(record)

save_record("04abf37b-a1de-40c0-86c6-2353f7b15c91.fcs", record['fcs_metadata'], record['s3_metadata'])
