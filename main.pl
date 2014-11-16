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

my @MORAS = qw(ya yu yo wa wo nn);
foreach my $c ('',qw(k s t n h m r)){ foreach (qw(a i u e o)) { push(@MORAS,$c.$_); } }

my $content;
my $p = XML::RSS::Parser->new;
my $feed; my @works = ();

sub write_to_file
{
	my $fn = shift; my %data = @_ ;
	open ( DMM, ">$fn" ) || die "Can't open: $!\n";
	print DMM JSON->new->utf8->encode( %data );
	close( DMM );
}

sub read_from_file
{
	my $fn = shift; 
	my $_text = do { open( DMM, "<:encoding(UTF-8)", $fn) or die("Error"); local $/; <DMM> };
	return %{JSON->new->decode($_text)};
}

sub get_count
{
	my ( $type, $id, $domain ) = @_ ;
	my $ct; my @count = (0,0);
	  
	if ( $domain & 1 )
	{
		$ct = get( "$DMM/$DOM[0]/list/=/article=$type/id=$id" );
		($count[0]) = $ct =~ m/(\d+).*タイトル中/ig ;
	}

	if ( $domain & 2 )
	{
		$ct = get( "$DMM/$DOM[1]/list/=/article=$type/id=$id" );
		($count[1]) = $ct =~ m/(\d+).*?タイトル中/ ;
	}

	if ( $domain == 3 ){ return @count; } else { return $count[$domain-1]; }
}

sub get_genres
{
	my %genres;

	$content = get( "$DMM/$DOM[0]/genre/" );
	foreach ( $content =~ m/article=keyword(.+?)<\/a>/mg )
	{
		my @g = $_ =~ m/id=(\d+).">(.+)/m; chomp $g[1];
		if ( $g[0] ne '' and $g[1] ne '' ){ $genres{$g[0]} = $g[1]; }
	}

	$content = get( "$DMM/$DOM[1]/genre/" );
	foreach ( $content =~ m/article=keyword(.+?)<\/a>/mg )
	{
		my @g = $_ =~ m/id=(\d+).">(.+)/m; chomp $g[1];
		if ( $g[0] ne '' && ( ! $genres{$g[0]} ) ){ $genres{$g[0]} = $g[1]; }
	}

	return \%genres;
}

sub get_makers
{
	my %makers;

	foreach ( @MORAS )
	{

		$content = get( "$DMM/$DOM[0]/maker/=/keyword=$_/" );

		foreach ( $content =~ m/(?s)class="d-unit">(.+?)<!--\/d-unit-->/mg )
		{
			my @m = $_ =~ m/(?s)id=(\d+).+?src="(.+?)".+?llarge">(.+?)<.+?\n(.*)<\/div>/m;

			my $id = shift(@m); if ( $id eq '' ){ next; }

			if ( $m[2] ne '' ){ $m[2] =~ s/.*<p>(.+?)<\/p>.*/\1/; }
			if ( $m[0] =~ m/noimage/ ){ $m[0] = ''; }

			$m[3] = 1;

			my %maker; @maker{qw(img name description domain)} = @m;
			$makers{$id} = \%maker;

		}

		$content = get( "$DMM/$DOM[1]/maker/=/keyword=$_/" );

		foreach ( $content =~ m/(?s)class="w50">(.+?)class="clear"/mg )
		{
			my @m = $_ =~ m/(?s)id=(\d+).+?src="(.+?)".+?bold">(.+?)<.+?\n(.*)<\/div>.*/m;

			my $id = shift(@m); if ( $id eq '' ){ next; }

			if ( $makers{$id} ){ $makers{$id}{"domain"} = 3; next; }
			
			if ( $m[2] ne '' ){ $m[2] =~ s/.*<p>(.+?)<\/p>.*/\1/; }
			if ( $m[0] =~ m/noimage/ ){ $m[0] = ''; }

			$m[3] = 2;

			my %maker; @maker{qw(img name description domain)} = @m;
			$makers{$id} = \%maker;
		}
	}

	return \%makers;
}

sub get_actresses
{
	my %acts;

	foreach ( @MORAS )
	{
		$content = get( "$DMM/$DOM[0]/actress/=/keyword=$_/" );

		foreach ( $content =~ m/article=actress(.+?)<\/a>/mg )
		{
			my @a = $_ =~ m/id=(\d+).+?src="(.+?)".+?"><br>(.+)/m;

			my $id = shift(@a); if ( $id eq '' ){ next; }

			if ( $a[0] =~ m/noimage/ ){ $a[0] = ''; }

			$a[2] = 1;

			my %actress; @actress{qw(img name domain)} = @a;
			$acts{$id} = \%actress;
		}

		$content = get( "$DMM/$DOM[1]/actress/=/keyword=$_/" );

		foreach ( $content =~ m/article=actress(.+?)<\/a>/mg )
		{
			my @a = $_ =~ m/id=(\d+).+?src="(.+?)".+?"><br>(.+)/m;

			my $id = shift(@a); if ( $id eq '' ){ next; }

			if ( $acts{$id} ){ $acts{$id}{"domain"} = 3; next; }

			if ( $a[0] =~ m/noimage/ ){ $a[0] = ''; }

			$a[2] = 2;

			my %actress; @actress{qw(img name domain)} = @a;
			$acts{$id} = \%actress;
		}
	}

	return \%acts;
}

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

#get_pages( "$DMM/$DOM[0]/list/$RSS[0]/$PARAMS/id=$id", 1, $count, 125 );
#get_pages( "$DMM/$DOM[1]/list/$RSS[1]/$PARAMS/id=$id", 1, $count, 125 );
