import re
from projects.models import EnterpriseUser

class EnterpriseUserLogic():
    def validatePasswordConfirmation(self, enterpriseUserData):
        return enterpriseUserData['password'] != enterpriseUserData['password_confirmation']

    def generateValidCompanyId(self, enterpriseUserData):
        if 'company_name' not in enterpriseUserData:
            return ''
        
        sanitazed_name = re.sub('[^A-Za-z0-9]+', '', enterpriseUserData['company_name'])
        data = EnterpriseUser.objects.all().filter(company_id=sanitazed_name).count()
        
        if data == 0:
            enterpriseUserData['company_id'] = sanitazed_name
        else:
            numVal = 0
            company_id = ''
            nameIsValid = False
            while not nameIsValid:
                numVal+=1
                company_id = sanitazed_name + str(numVal)
                data = EnterpriseUser.objects.all().filter(company_id=company_id).count()
                if data == 0:
                    nameIsValid = True
            
            enterpriseUserData['company_id'] = sanitazed_name + str(numVal)
        
        return enterpriseUserData