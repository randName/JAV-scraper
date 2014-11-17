#!/usr/bin/perl
use strict; use utf8;
use JSON;
use LWP::Simple;
use XML::RSS::Parser;

binmode(STDOUT,":utf8");

my $DMM = "http://www.dmm.co.jp";
my @DOM = ( "digital/videoa/-", "mono/dvd/-" );
my @RSS = ( "rss/=", "=/rss=create" );

my @PAGES_URL; 
foreach ( qw(0 1) ){ $PAGES_URL[$_] = "$DMM/$DOM[$_]/list/$RSS[$_]/article=maker/sort=release_date"; }

my @MORAS = qw(ya yu yo wa wo nn);
foreach my $c ('',qw(k s t n h m r)){ foreach (qw(a i u e o)) { push(@MORAS,$c.$_); } }

my $content;
my $p = XML::RSS::Parser->new;

sub write_to_file
{
	my $fn = shift; open ( DMM, ">$fn" ) or die "Can't open: $!\n";
	print DMM JSON->new->utf8->encode( @_ ); close( DMM );
}

sub read_from_file
{
	my $fn = shift; 
	my $_text = do { open( DMM, "<:encoding(UTF-8)", $fn) or die("Can't open: $!\n"); local $/; <DMM> };
	return JSON->new->decode($_text);
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

	# if ( $domain == 3 ){ return @count; } else { return $count[$domain-1]; }
	return @count;
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

sub update_counts
{
	my $makers = shift;
	my @update; my @updated;

	for my $id ( keys %{$makers} )
	{
		my @s_c = get_count( "maker", $id, $makers->{$id}{'domain'} );

		if ( exists($makers->{$id}{'count'}) )
		{
			if ( not ( @s_c ~~ @{$makers->{$id}{'count'}} ) )
			{
				print "$id updated:";
				foreach ( qw(0 1) )
				{
					$update[$_] = $s_c[$_] - @{$makers->{$id}{'count'}}[$_];
					if ( $update[$_] ne 0 ){ print "\t$_\t+$update[$_]"; }
				}
				push( @updated, $id );
				print "\n";
			}
		}
		else
		{
			print "$id initialized with ( $s_c[0], $s_c[1] ).\n";
		}
		
		@{$makers->{$id}{'count'}} = @s_c;
	}

	return @updated;
}

sub get_pages
{
	my $feed;
	my ( $works, $q, $i_start, $i_end, $step ) = @_ ;

	my $p_end = int( $i_end/$step );
	if ( $i_end%$step > 0 ){ $p_end += 1; }

	# print "$i_start\t$i_end\t$p_end\t$step\n";

	for ( my $i = int( $i_start/$step )+1; $i <= $p_end; $i++ )
	{
		$feed = $p->parse_uri( "$q/limit=$step/page=$i/" );

		if ( not defined $feed )
		{
			if ( $step != 1 )
			{
				get_pages( $works, $q, ($i-1)*$step+1, $i*$step, $step/5 );
			}
			else { print "error at $i\n"; }
		}
		else
		{
			foreach ( $feed->query('//item') ){ push( @{$works}, get_items($_) ); }
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
	($v{'runtime'}) = $content =~ m/>([0-9]+)分/ ;
	($v{'label'}) = $content =~ m/article=label\/id=([0-9]+)/g ;
	($v{'series'}) = $content =~ m/article=series\/id=([0-9]+)/g ;
	$v{'actress'} = [ $content =~ m/article=actress\/id=([0-9]+)/g ];

	$v{'tags'} = [ $content =~ m/article=keyword\/id=([0-9]+)/g ];

	#print "$_ $v{$_}\n" for keys %v; print "\n";
	#print "$v{'cid'}\t$v{'title'}\n";
	
	return \%v;
}

sub get_works
{
	my $makers = shift;

	for my $id ( keys %{$makers} )
	{
 		my @works = ();

		print "$id: ";

		foreach ( qw(0 1) )
		{
			get_pages( \@works, "$PAGES_URL[$_]/id=$id", 1, @{$makers->{$id}{'count'}}[$_], 125 );
		}

		# foreach ( @works ) { print "$_ $work->{$_}\t" for ( keys %{$work} ); print "\n"; }

		write_to_file( "works/$id.json", \@works );
		
		print @works." works written.\n";
	}
}

#my %keywords = %{&get_genres}; write_to_file("genres.json", \%keywords );

$|=1;

my %studios; my %st_updated;

if ( -e "makers.json" )
{
	print "Reading from file...";
	%studios = %{&read_from_file("makers.json")};
	print " OK.\n";

	print "Getting online version...";
	%st_updated = %{&get_makers};
	print " OK.\n";

	if ( %studios != %st_updated )
	{
		print "Maker list updated\n";

		# update maker list
	}
	else
	{
		print "Local database matches online. Continuing.\n";
	}
}
else
{
	print "Database not found. Getting online version...";
	%studios = %{&get_makers};
	print " OK.\n";
}

print "Updating counts...\n";
my @updated = update_counts(\%studios);
print " OK.\n";
%st_updated = map { $_ => $studios{$_} } @updated;
print @updated." makers require update. Updating...\n";
get_works(\%st_updated); 
print " OK.\n";
write_to_file("makers.json", \%studios);
