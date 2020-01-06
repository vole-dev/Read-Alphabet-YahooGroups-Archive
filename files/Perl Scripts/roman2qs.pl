#!/usr/bin/perl -w
use encoding 'utf8';
use warnings;
use strict;

sub read_dict {
	my $ret = {};
	while (<::DATA>) { $ret->{lc $_[0]} = $_[1] if (@_ = split) > 1 }
	return $ret;
}

sub roman_to_qs {
	my $dict = shift;
	return map { (exists $dict->{lc $_}) ? ($dict->{lc $_}) : ($_) } @_;
}

$| = 1;
my $q = "(?:(?<=[\\w'])(?![\\w']))|(?:(?<![\\w'])(?=[\\w']))";
my $dict = read_dict;

while (<>) { print roman_to_qs ($dict, split /$q/o) }

__DATA__
