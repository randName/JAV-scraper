open ( MAKER, ">maker_dvd_counts" ) || die "Can't open: $!\n";

{
		$count = get( "$DMM/list/=/article=maker/id=$id" );
		($count) = $count =~ m/(\d+).*?タイトル中/ ;
		print MAKER "$id\t$count\n";
}
close( MAKER );
