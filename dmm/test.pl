#!/usr/bin/perl
use strict;
use JSON;
use XML::RSSLite;
use LWP::Simple;

binmode(STDOUT,":utf8");

my $RSS = "http://www.dmm.co.jp/digital/videoa/-/list/rss/=/article=maker/limit=1/sort=release_date/id=4469/page=278/";

my %result;

parseRSS( \%result, get( $RSS ) );

print "=== Channel ===\n",
        "Title: $result{'title'}\n",
        "Desc:  $result{'description'}\n",
        "Link:  $result{'link'}\n\n";

foreach (@{$result{'item'}}) {
  print "  --- Item ---\n",
        "  Title: $_->{'title'}\n",
        "  Desc:  $_->{'description'}\n",
        "  Link:  $_->{'link'}\n\n";
}

