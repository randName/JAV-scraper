#!/usr/bin/perl
use strict; use utf8;
use JSON;

binmode(STDOUT,":utf8");

open ( DMM, "<dmm.json" ) || die "Can't open: $!\n";
my $data = JSON->new->utf8->decode(<DMM>); close( DMM );

foreach my $id ( keys $data->{'makers'} )
{
	my $m = $data->{'makers'}->{$id};
	print "$id\t$m->{'domain'}\t$m->{'name'}\n";
}
