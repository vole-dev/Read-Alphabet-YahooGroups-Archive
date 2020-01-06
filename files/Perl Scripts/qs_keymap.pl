#!/usr/bin/perl -w
use strict;
use warnings;

my @keys = (
	[ "Utter", 0x2A ], [ "It", 0x20 ], [ "Roe", 0x18 ], [ "No", 0x16 ],
	[ "Tea", 0x02 ], [ "See", 0x0A ], [ "Low", 0x17 ], [ "Eight", 0x23 ],
	[ "At", 0x24 ], [ "Day", 0x03 ], [ "They", 0x07 ], [ "Jay", 0x0F ],
	[ "May", 0x15 ], [ "Key", 0x04 ], [ "Eat", 0x21 ], [ "Et", 0x22 ],
	[ "Way", 0x11 ], [ "Vie", 0x09 ], [ "Pea", 0x00 ], [ "I", 0x25 ],
	[ "Ox", 0x28 ], [ "He", 0x12 ], [ "Fee", 0x08 ], [ "Bay", 0x01 ],
	[ "Ing", 0x14 ], [ "Awe", 0x27 ], [ "She", 0x0C ], [ "Ooze", 0x2E ],
	[ "Gay", 0x05 ], [ "Owe", 0x2C ], [ "Ye", 0x10 ], [ "Ah", 0x26 ],
	[ "Cheer", 0x0E ], [ "Jay", 0x0F ], [ "Out", 0x2B ], [ "Foot", 0x2D ],
	[ "Thaw", 0x06 ], [ "Oy", 0x29 ], [ "Jai", 0x0D ], [ "Why", 0x13 ]
);

print "partial default alphanumeric_keys xkb_symbols \"basic\" {\n\n";
print "\tname[Group1]=\"QuikScript\";\n\n";

foreach my $level qw ( AC AB AD AE ) {
	foreach my $code qw( 04 07 05 06 03 08 02 09 01 10) {
		my ($name, @key) = @{shift @keys};
		print	"\tkey <",
			$level, $code,
			"> { [ ",
			join (', ',
				map { sprintf "0x%X", (0x0100E650 + $_) } @key
			), " ] }; // ", $name, "\n";
	}
}

print "};\n";
