similar_elements = [{'element_name_l1': ' Id', 'element_name_l2': ' Id'}, {'element_name_l1': 'First Name', 'element_name_l2': 'Firstname'}, {'element_name_l1': 'Last Name', 'element_name_l2': 'Lastname'}, {'element_name_l1': 'Hod Email Id', 'element_name_l2': 'Email'}, {'element_name_l1': 'Job Role', 'element_name_l2': 'Mobile'}, {'element_name_l1': 'Full Name', 'element_name_l2': 'Lastname'}, {'element_name_l1': 'Marital Status', 'element_name_l2': 'Status'}, {'element_name_l1': 'Office Country', 'element_name_l2': 'Country'}, {'element_name_l1': 'Current Country', 'element_name_l2': 'Country'}, {'element_name_l1': 'Current State', 'element_name_l2': 'Created'}]


def parse_elements(elements_list):
    l1_matched = []
    l2_matched = []
    
    for element in elements_list:
        l1_matched.append(element['element_name_l1'])
        l2_matched.append(element['element_name_l2'])
    
    return l1_matched, l2_matched

l1_matched, l2_matched = parse_elements(similar_elements)
print("L1 Matched:", l1_matched)
print()
print("L2 Matched:", l2_matched)

def find_unmatched_elements(original_list, matched_list):
    unmatched = [element for element in original_list if element not in matched_list]
    return unmatched

# Example usage:
l1_original = ['Id','First Name','Last Name','Band','Employee Id','Business Unit','Ctc','Cost Center Id','Date Of Exit','Date Of Joining','Date Of Activation','Departments Hierarchy','Direct Manager Employee Id','Employee Type','Grade','Group Company','Hod Email Id','Hod','Hod Employee Id','Hrbp Employee Id', 'Job Role', 'Job Role Code', 'Job Role Name', 'Job Level Code', 'L2 Manager Employee Id', 'Separation Agreed Last Date', 'Separation Status', 'Total Ctc', 'Candidate Id', 'Center Type', 'Company Email Id', 'Date Of Birth', 'Date Of Resignation', 'City Type', 'Dependents', 'Education Details', 'Emergency Contact Number', 'Emergency Contact Person', 'Emergency Contact Relation', 'Full Name', 'Gender', 'Location Type', 'Marital Status', 'Middle Name', 'Office Address', 'Office Area', 'Office City', 'Office Country', 'Office Location', 'Office State', 'Primary Mobile Number', 'User Unique Id', 'Work Area Code', 'Current Address', 'Current Country', 'Current State', 'Personal Email Id', 'Personal Mobile No', 'Office Mobile No', 'Bank Name', 'Bank Branch', 'Bank Account', 'Bank Ifsc', 'Bank Pan', 'Aadhaar Number', 'Job Level', 'Function', 'Leadership Group', 'Nationality', 'Function Code', 'Direct Manager Email', 'Direct Manager Name', 'Permanent Pin Code', 'Latest Modified Any Attribute', 'Regular/ Temporary', 'Blood Group', 'Departments Hierarchy With Codes', 'Notice Period Assigned', 'Salutation', 'Permanent Address', 'Permanent City', 'Permanent Country', 'Permanent State', 'Date Of Death', 'Anniversary Date', 'Group Company Code', 'Functional Head', 'Employment Type', 'Contract End Date', 'Contract Start Date', 'Attendance Shift', 'Role', 'Dependent Role', 'Cost Center', 'Office Location Cost Center', 'Is Rehire', 'Rehire By', 'Rehire On', 'Rehire Reason', 'Employee Separation Reason', 'Admin Deactivation Type', 'Dm Pool', 'Home', 'Sub Employee Type', 'Hrbp Email Id', 'Source', 'Source Type', 'Fnf Status', 'Past Work', 'Passport Address', 'Passport Country', 'Passport Number', 'Passport Type', 'Federation Id', "Father'S Name", 'Job Role Alias', 'Channel', 'Fls/Nfls', 'Short Desg.', 'Zone', 'Region', 'Recruiter', 'Zrm', 'Hrbp', 'Zhr', 'Uan Number', 'Esic Number', 'Pf Number', 'Activation Timestamp', 'Designation Title', 'Latest Modified Timestamp']

l2_original = ['Id', 'Displayname', 'Firstname', 'Lastname', 'Country', 'Mobile', 'Email', 'Status', 'Created', 'Updated', 'Created By', 'Updated By', 'Assignedgroups', 'Provisionedapps', 'Attributes', 'Rbacroles', 'Version', ' Class']


l1_matched = ['Id', 'First Name', 'Last Name', 'Hod Email Id', 'Job Role', 'Full Name', 'Marital Status', 'Office Country', 'Current Country', 'Current State']
l2_matched = [' Id', 'Firstname', 'Lastname', 'Email', 'Mobile', 'Lastname', 'Status', 'Country', 'Country', 'Created']


l1_unmatched = find_unmatched_elements(l1_original, [elem.strip() for elem in l1_matched])
l2_unmatched = find_unmatched_elements(l2_original, [elem.strip() for elem in l2_matched])

print()
print("Unmatched Elements L1:", l1_unmatched)
print()
print("Unmatched Elements L2:", l2_unmatched)



