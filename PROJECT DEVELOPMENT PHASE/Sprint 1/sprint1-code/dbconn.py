import credential
import ibm_db
import ibm_boto3
from ibm_botocore.client import Config, ClientError
from datetime import *

# conn = ibm_db.connect("DATABASE="+credential.DB2_DATABASE_NAME+";HOSTNAME="+credential.DB2_HOST_NAME+";PORT="+credential.DB2_PORT+";SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID="+credential.DB2_UID+";PWD="+credential.DB2_PWD+"",'','')
conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=21fecfd8-47b7-4937-840d-d791d0218660.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=31864;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=lvh24264;PWD=gZS5lI5g0AJ3CrRN",'','')
# cos = ibm_boto3.resource("s3",
#     ibm_api_key_id=credential.COS_API_KEY_ID,
#     ibm_service_instance_id=credential.COS_INSTANCE_CRN,
#     config=Config(signature_version="oauth"),
#     endpoint_url=credential.COS_ENDPOINT
# )
# class Database:
#     def _init_(self) -> None:
#         pass
#     def loginUser(self,email,password):
#         sql = "SELECT email,password FROM credential WHERE email=?"
#         stmt = ibm_db.prepare(conn, sql)
#         ibm_db.bind_param(stmt,1,email)
#         ibm_db.execute(stmt)
#         account = ibm_db.fetch_assoc(stmt)
#         if account:
#             print(account)
#             return account
#         return None
    




