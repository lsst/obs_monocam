import os
import re
from lsst.pipe.tasks.ingest import ParseTask, RegisterTask
from lsst.pipe.tasks.ingestCalibs import CalibsParseTask

# XXX This is completely made up
filters = {
    0: 'u',
    1: 'g',
    2: 'r',
    3: 'i',
    4: 'z',
    5: 'y',
    "UNK": "UNKNOWN",
}

EXTENSIONS = ["fits", "gz", "fz"]

class MonocamParseTask(ParseTask):
    _counter = -1  # Visit counter; negative so it doesn't overlap with the 'id' field, which autoincrements

    def getInfo(self, filename):
        # Grab the basename
        phuInfo, infoList = ParseTask.getInfo(self, filename)
        basename = os.path.basename(filename)
        while any(basename.endswith("." + ext) for ext in EXTENSIONS):
            basename = basename[:basename.rfind('.')]
        phuInfo['basename'] = basename
        return phuInfo, infoList

    def translate_visit(self, md):
        visit = self._counter
        self._counter -= 1
        return visit

    def translate_ccd(self, md):
        return 0  # There's only one

    def translate_filter(self, md):
        return filters[md.get("FILTER")]

class MonocamRegisterTask(RegisterTask):
    def addVisits(self, conn, dryrun=False, table=None):
        # Set the visit numbers to match the 'id' field
        if table is None:
            table = self.config.table
        sql = "UPDATE %s SET visit = id" % table
        if dryrun:
            print "Would execute: %s" % sql
        else:
            conn.execute(sql)
        return RegisterTask.addVisits(self, conn, dryrun=dryrun, table=table)


class MonocamCalibsParseTask(CalibsParseTask):
    def _translateFromCalibId(self, field, md):
        data = md.get("CALIB_ID")
        match = re.search(".*%s=(\S+)" % field, data)
        return match.groups()[0]

    def translate_ccd(self, md):
        return self._translateFromCalibId("ccd", md)

    def translate_filter(self, md):
        return self._translateFromCalibId("filter", md)

    def translate_calibDate(self, md):
        return self._translateFromCalibId("calibDate", md)
