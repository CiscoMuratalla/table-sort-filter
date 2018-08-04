import os, sys
import webbrowser
import platform
from tempfile import gettempdir
from datetime import datetime
from collections import namedtuple
from timeit import default_timer as timer


DEFAULT_SCREEN_STACK_SIZE = 20

FILE_LINK = "file:///"

HTML_HEADER = """\
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
</head>
<body>
""".splitlines()


HTML_TRAILER = """\
</body>
</html>
""".splitlines()


field_names = [
               'Facility', 'Test_group', 'Test_number',
              'Description', 'Result', 'Execution_time',
              'Information', 'Output'
]

Test_record = namedtuple('Test_record', field_names )


def _write_HTML_header(fp):
   for line in HTML_HEADER: fp.write(line)


def _write_HTML_trailer(fp):
   for line in HTML_TRAILER: fp.write(line)


def return_seconds_as_h_m_s(seconds):
    '''
    return tuple h, m, s representing hours, minutes, seconds
    '''
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return h, m, s


class Test_Output:
    '''
    Manage and generate test output data
    '''
    def __init__(self):
        self.test_output_dir = None
        self.test_output = None
        self.screen_trace_stack = []
        self.screen_trace_stack_size = DEFAULT_SCREEN_STACK_SIZE
        self.output_records = []
        self.report_start = 0
        self.init_output()


    def init_output(self):
        '''
        Initialized test output area
        '''
        self.test_output = []
        self.screen_trace_stack = []


    def _format_text_html(self, text, size = None):
        '''
        format text to html
        '''
        #
        # TODO add HTML text formatting: color, font, size
        #

        if isinstance(text,str):
            text = text.splitlines()

        #
        # add html new line tag
        #
        if size is None:
            text_size = 30

        return ['<p style="font-size:{0}px">'.format(text_size)] + \
                            [ line + '<br>' for line in text] + \
                            ['</p>']


    def add_text(self, text, size = None):
        '''
        Add text to test output
        '''
        self.test_output += self._format_text_html(text, size = size)


    def add_screen_trace_stack(self, screen):
        ''' Add screen print to screen stack
        '''
        self.screen_trace_stack.append(screen)
        if (
            len(self.screen_trace_stack)
            ==
            self.screen_trace_stack_size*3
        ):
           self.screen_trace_stack = self.screen_trace_stack[
                                          -self.screen_trace_stack_size:
           ]


    def _write_screen_trace_stack(self, fp):
       for screen in self.screen_trace_stack[
                                          -self.screen_trace_stack_size:
       ]:
          for line in screen:
             fp.write(line.encode('ascii', 'ignore').decode() + '\n')


    def add_screen(self, screen):
        '''
        Add screen print to test output. screen is a list of data
        no html header should be included in screen
        '''

        #
        # slice out html header and trailer
        #
        self.test_output += screen


    def write_file(self, filename):
        '''
        Write test output created. '.htm' is appended to filename
        '''

        #
        # Add html trailer
        #

        if self.test_output_dir is None:
            self.set_dir('Test_Output')

        os.makedirs(self.test_output_dir, exist_ok = True)

        full_filename = self.test_output_dir + os.sep + filename + '.htm'

        with open(full_filename, 'w') as fp:
           _write_HTML_header(fp)
           for line in self.test_output:
               fp.write(line.encode('ascii', 'ignore').decode() + '\n')

           fp.write(
                    ''.join(
                            self._format_text_html(
                                   'Screen trace stack. Size = {}'
                                   .format(self.screen_trace_stack_size)
                            )
                    )
           )
           self._write_screen_trace_stack(fp)
           _write_HTML_trailer(fp)

        print('Test output written to: ' + full_filename)

        return full_filename


    def set_dir(self, prefix_dir = None):
        '''
        Set output direcory
        '''
        self.test_output_dir = (
                                gettempdir()
                                + os.sep
                                + (
                                   '' if prefix_dir is None
                                   else prefix_dir
                                )
                                + os.sep
                                + 'D'
                                + datetime
                                .strftime(datetime.now(), '%Y%m%d')
                                + os.sep
                                + 'T'
                                + datetime
                                .strftime(datetime.now(), '%H%M%S')
        )


    def init_report(self, prefix_dir = None):
        '''
        initialize data for report
        '''
        self.output_records = []

        # set output directory
        self.set_dir(prefix_dir)

        self.report_start = timer()


    def add_report_record(self, *args, **kwargs):
       '''
       Add report record information. All parameters from this list
       must be specified:
       '''

       # Accept Test_record as one parameter
       if len(args) == 1 and isinstance(args[0], Test_record):
          self.output_records.append(args[0])

       # other wise accept field from tuple as parm
       else:
          tuple_parms = ""
          for fn in field_names:
              tuple_parms += fn + " = kwargs['" + fn + "'], "

          self.output_records.append(eval("Test_record(" + tuple_parms +
                                                     ")"
                                         )
                                    )


    def write_report(self, display_report = True):
        '''
        Write report, calculate total count, failed, and total report time
        '''

        report_end = timer()
        test_count = fail_count = skip_count = 0

        html_output = """ \
                      <!DOCTYPE html>
                      <html>
                      <head>
                          <style>
                      td {
                          width: 200px;
                          height: 60px;
                      }
                      th {
                      cursor: pointer;
                      }
                      .selected{
                        background-color: #008000;
                      }
                      .bad{
                       background-color: #FF0000;
                      }
                          </style>
                          </head>
                      <body>
                      <input type="text" id="myInput" onkeyup="myFunction()" placeholder="Search..." title="Type in a name">
                          <table border="1" id="myTable">

                                  <tr>

                      """.splitlines()


        #
        # add column headers
        #
        for fn in field_names:
            html_output.append("<th>" + fn + "</th>")

        html_output += """ \
                                   </tr>


                       """.splitlines()
        #
        # Create table with test information records
        #
        for tr in self.output_records:
            test_count += 1
            new_row, row_result = '', None # added row_result
            for fn in field_names:
                if fn == 'Result':
                    if tr.Result > 4:
                        fail_count += 1
                        output_value, row_result = 'Fail', False # added row_result
                    elif tr.Result == 4:
                        skip_count += 1
                        output_value = 'Skipped'
                    else:
                        output_value, row_result = 'Success', True # added row_result
                elif fn == 'Output':
                    output_value = ''
                    if tr.Output != '':
                        output_value = '<a target="_blank" href=' + \
                                       FILE_LINK + tr.Output + \
                                       ' style="display:block;">Output</a>'
                elif fn == 'Execution_time':
                    output_value = ('%d:%02d:%02d' %
                                    return_seconds_as_h_m_s(tr.Execution_time)
                                   )
                else:
                    output_value = str(getattr(tr,fn))

                new_row += '<td>' + output_value + '</td>'
            result_class = '' if row_result is None else ' class="{0}"'.format('selected' if row_result else 'bad') # added result_class
            new_row = '<tr{0}>{1}</tr>'.format(result_class, new_row)
            html_output.append(new_row)


        html_output += self._format_text_html(
                 "Total tests: %d. Failed tests: %d. Skipped tests: %d."
                 % (test_count, fail_count, skip_count)
        )

        html_output += self._format_text_html(
                                       'Report test time %d:%02d:%02d' %
                                    return_seconds_as_h_m_s(report_end -
                                                     self.report_start))
        html_output += """ \


<script type='text/javascript'>

        const getCellValue = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;

const comparer = (idx, asc) => (a, b) => ((v1, v2) =>
    v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2)
    )(getCellValue(asc ? a : b, idx), getCellValue(asc ? b : a, idx));

// do the work...
document.querySelectorAll('th').forEach(th => th.addEventListener('click', (() => {
    const table = th.closest('table');
    Array.from(table.querySelectorAll('tr:nth-child(n+2)'))
        .sort(comparer(Array.from(th.parentNode.children).indexOf(th), this.asc = !this.asc))
        .forEach(tr => table.appendChild(tr) );
})));


</script>

<script>
function myFunction() {
  var input, filter, table, tr, td, i;
  input = document.getElementById("myInput");
  filter = input.value.toUpperCase();
  table = document.getElementById("myTable");
  tr = table.getElementsByTagName('tr');
  for (i = 0; i < tr.length; i++) {
    td = tr[i].getElementsByTagName('td');
    var match = false;
    for(var j = 0; j < td.length; j++) {
    if (td[j]) {
      if (td[j].innerHTML.toUpperCase().indexOf(filter) > -1) {
        match = true;
      }
    }
}
    if (match) {
        tr[i].style.display = '';
    } else {
      tr[i].style.display = 'none';
      }
    }
  }

</script>
</table>
                       </body>
                       </html>
                       """.splitlines()


        #
        # create and write report file
        #
        os.makedirs(self.test_output_dir, exist_ok = True)
        full_filename = self.test_output_dir + os.sep + 'test_report.htm'

        with open(full_filename, 'w') as fp:
           for line in html_output: fp.write(line + '\n')


        if display_report:
            #
            # Check if mac os X
            #
            webbrowser.open(FILE_LINK + full_filename)

        #
        # Return full filename of report
        #
        return full_filename
