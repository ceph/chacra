from datetime import datetime, timedelta
import logging
from pecan import conf

logger = logging.getLogger(__name__)


def repository_is_automatic(project_name, repo_config=None):
    repo_config = repo_config or getattr(conf, 'repos', {})
    logger.debug('checking if repository is automatic for project: %s', project_name)
    # every repo is automatic by default unless explicitly configured otherwise
    if repo_config.get(project_name, {}).get('automatic', True):
        logger.info('project: %s is configured for automatic repositories', project_name)
        return True
    logger.info('project: %s has automatic repository feature disabled', project_name)
    return False


def last_seen(timestamp):
    now = datetime.utcnow()
    difference = now - timestamp
    formatted = ReadableSeconds(difference.seconds)
    return "%s ago" % formatted


class ReadableSeconds(object):

    def __init__(self, seconds):
        self.original_seconds = seconds

    @property
    def relative(self):
        """
        Generate a relative datetime object based on current seconds
        """
        return datetime(1, 1, 1) + timedelta(seconds=self.original_seconds)

    def __str__(self):
        return "{years}{months}{days}{hours}{minutes}{seconds}".format(
            years=self.years,
            months=self.months,
            days=self.days,
            hours=self.hours,
            minutes=self.minutes,
            seconds=self.seconds,
        ).rstrip(' ,')

    @property
    def years(self):
        # Subtract 1 here because the earliest datetime() is 1/1/1
        years = self.relative.year - 1
        year_str = 'years' if years > 1 else 'year'
        if years:
            return "%d %s, " % (years, year_str)
        return ""

    @property
    def months(self):
        # Subtract 1 here because the earliest datetime() is 1/1/1
        months = self.relative.month - 1
        month_str = 'months' if months > 1 else 'month'
        if months:
            return "%d %s, " % (months, month_str)
        return ""

    @property
    def days(self):
        # Subtract 1 here because the earliest datetime() is 1/1/1
        days = self.relative.day - 1
        day_str = 'days' if days > 1 else 'day'
        if days:
            return "%d %s, " % (days, day_str)
        return ""

    @property
    def hours(self):
        hours = self.relative.hour
        hour_str = 'hours' if hours > 1 else 'hour'
        if hours:
            return "%d %s, " % (self.relative.hour, hour_str)
        return ""

    @property
    def minutes(self):
        minutes = self.relative.minute
        minutes_str = 'minutes' if minutes > 1 else 'minute'
        if minutes:
            return "%d %s, " % (self.relative.minute, minutes_str)
        return ""

    @property
    def seconds(self):
        seconds = self.relative.second
        seconds_str = 'seconds' if seconds > 1 else 'second'
        if seconds:
            return "%d %s, " % (self.relative.second, seconds_str)
        return ""

