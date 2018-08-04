import os
import sys
import random

#
# update PYTHONPATH
#
sys.path.append(os.getcwd())

from aatest_output import Test_Output, Test_record


desc_choices = ('Cat', 'Dog', 'Pig', 'Horse', 'Mule')

info_choices = ('Red', 'Blue', 'Purple', 'Brown', 'Maroon')

facil_choices = ('Kitchen', 'Shower', 'Room', 'Den', 'Patio')

test_report = Test_Output()

test_report.init_report('Test_Report')

for i in range(10):
   test_report.add_report_record(
              Test_record(
                          Facility = random.choice(facil_choices),
                          Test_group = int(random.random() * 10**3),
                          Test_number = i,
                          Description = random.choice(desc_choices),
                          Result = random.choice((0,8)),
                          Execution_time = int(random.random() * 10**3),
                          Information = random.choice(info_choices),
                          Output = ''
              )
   )


test_report.write_report(display_report = True)
