#!/usr/bin/perl
use strict; use utf8;
use JSON;
use LWP::Simple;
use XML::RSS::Parser;

binmode(STDOUT,":utf8");

my $DMM = "http://www.dmm.co.jp";
my @DOM = ( "digital/videoa/-", "mono/dvd/-" );
my @RSS = ( "rss/=", "=/rss=create" );
my $PARAMS = "article=maker/sort=release_date";

my $p = XML::RSS::Parser->new;

my $feed; my @works = ();
#my $json = JSON->new->utf8->encode(\@works); 

#get_pages( "$DMM/$DOM[0]/list/$RSS[0]/$PARAMS/id=$id", 1, $count, 125 );
#get_pages( "$DMM/$DOM[1]/list/$RSS[1]/$PARAMS/id=$id", 1, $count, 125 );
sub get_pages
{
	my ( $q, $i_start, $i_end, $step ) = @_ ;

	my $p_end = int( $i_end/$step );
	if ( $i_end%$step > 0 ){ $p_end += 1; }

	print "$i_start\t$i_end\t$p_end\t$step\n";

	for ( my $i = int( $i_start/$step )+1; $i <= $p_end; $i++ )
	{
		$feed = $p->parse_uri( "$q/limit=$step/page=$i/" );

		if ( not defined $feed )
		{
			if ( $step != 1 )
			{
				get_pages( $q, ($i-1)*$step+1, $i*$step, $step/5 );
			}
			else { print "error at $i\n"; }
		}
		else
		{
			foreach ( $feed->query('//item') ){ push( @works, get_items($_) ); }
		}
	}
}

sub get_items
{
	my %v; my $content = $_->query('content:encoded')->text_content;

	$v{'title'} = $_->query('title')->text_content;
	$v{'url'} = $_->query('link')->text_content;
	$v{'description'} = $_->query('description')->text_content;
	$v{'date'} = $_->query('dc:date')->text_content;

	($v{'cid'}) = $v{'url'} =~ m/cid=([^\/]+)/ ;
	($v{'runtime'}) = $content =~ m/>([0-9]+)/ ;
	($v{'label'}) = $content =~ m/article=label\/id=([0-9]+)/g ;
	($v{'series'}) = $content =~ m/article=series\/id=([0-9]+)/g ;
	$v{'actress'} = [ $content =~ m/article=actress\/id=([0-9]+)/g ];

	$v{'tags'} = [ $content =~ m/article=keyword\/id=([0-9]+)/g ];

	#print "$_ $v{$_}\n" for keys %v; print "\n";
	#print "$v{'cid'}\t$v{'title'}\n";
	
	return \%v;
}

