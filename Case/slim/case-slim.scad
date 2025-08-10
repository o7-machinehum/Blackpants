/*
 * Slim case for WHY2025 badge
 *
 * Design: hxr.social/@thomasflummer
 *
 * License: CC-BY-SA
 *
 */


/*
 * Library function: half_rounded_cube
 * ==================================================================
 *
 * Used to make "cubes" with rounded corners in one plane
 *
 */
module half_rounded_cube(x, y, z, radius)
{
	hull()
	{
		for(xp = [-1, 1])
		{
			for(yp = [-1, 1])
			{
				for(zp = [-1, 1])
				{
					translate([xp*(x/2-radius), yp*(y/2-radius), zp*(z/2-0.1/2)])
						cylinder(r = radius, h = 0.1, center = true, $fn = 200);
				}
			}
		}
	}
}

/*
 * Library function: cylinder_fillet_side
 * ==================================================================
 *
 * Used to make smooth fillets offset along a cylinder
 *
 */
module cylinder_fillet_side(diameter, length, side_thickness, fillet_radius)
{
	fillet_angle = asin((fillet_radius+side_thickness/2)/(diameter/2+fillet_radius));
	difference()
	{
		union()
		{
			cylinder(d = diameter, h = length, center = true, $fn = 200);
			
			translate([0, -(cos(fillet_angle)*(diameter/2 + fillet_radius))/2, 0])
				cube([sin(fillet_angle)*diameter, cos(fillet_angle)*(diameter/2 + fillet_radius), length], center = true);
			
			
		}
		union()
		{
			for(i = [-1, 1])
			{	
				translate([0, 0, 0])
				rotate(i*fillet_angle, [0, 0, 1])
				translate([0, -diameter/2-fillet_radius, 0])
					cylinder(r = fillet_radius, h = length + 0.1, center = true, $fn = 200);
			}
		}
	}
}

/*
 * Library function: edge
 * ==================================================================
 *
 * Used to make roundes edges on objects
 *
 */
module edge(radius, height)
{
	difference()
	{
		translate([radius/2-0.5, radius/2-0.5, 0])
			cube([radius+1, radius+1, height], center = true);

		translate([radius, radius, 0])
			cylinder(h = height+1, r1 = radius, r2 = radius, center = true, $fn = 100);
	}
}

module case(twoPart)
{
	difference()
	{
		union()
		{
			minkowski()
			{
				union()
				{
					translate([0, -5/2, -10/2])
						cube([90-5, 148-5-5, 10], center = true);

					translate([0, (148-5)/2-5, -5])
					rotate(90, [0, 1, 0])
						cylinder(r = 5, h = 90-5, center = true, $fn = 100);

					translate([0, 0, -5/2])
						cube([90-5, 148-5, 5], center = true);

					for(xp = [-1, 1])
					{
						difference()
						{
							translate([xp*(90/2-12), -148/2+113/2, -18/2-1])
							rotate(90, [1, 0, 0])
							rotate(-90*xp, [0, 0, 1])
								cylinder_fillet_side(24-5, 113-5, 0, 10);
							
							translate([xp*(90/2-12), -148/2+110, -18/2-1-10])
							rotate(-30, [1, 0, 0])
							union()
							{
								translate([0, -10+40/2, -50/2])
									cube([40, 40, 50], center = true);
								
								translate([0, 0, 0])
									rotate(90, [0, 1, 0])
									cylinder(r = 10, h = 40, center = true, $fn = 100);
							}
						}
					}
				}
				
				sphere(r = 2.5, $fn = 40);
			}
		}
		union()
		{
			translate([0, 0, 20/2])
				cube([92, 150, 20], center = true);

			difference()
			{
				minkowski()
				{
					union()
					{
						translate([0, -5/2, -10/2])
							cube([90-5, 148-5-5, 10], center = true);

						translate([0, (148-5)/2-5, -5])
						rotate(90, [0, 1, 0])
							cylinder(r = 5, h = 90-5, center = true, $fn = 100);

						translate([0, 0, -5/2])
							cube([90-5, 148-5, 5], center = true);

						for(xp = [-1, 1])
						{
							difference()
							{
								translate([xp*(90/2-12), -148/2+98/2, -18/2-1])
								rotate(90, [1, 0, 0])
								rotate(-90*xp, [0, 0, 1])
									cylinder_fillet_side(24-5, 98-5, 0, 10);
								
								translate([xp*(90/2-12), -148/2+95, -18/2-1-10])
								rotate(-30, [1, 0, 0])
								union()
								{
									translate([0, -10+40/2, -50/2])
										cube([40, 40, 50], center = true);
									
									translate([0, 0, 0])
										rotate(90, [0, 1, 0])
										cylinder(r = 10, h = 40, center = true, $fn = 100);
								}
							}
						}
					}
					
					sphere(r = 1.3, $fn = 40);
				}
				union()
				{
					// corner mounting spots for inserts
					for(xp = [-1, 1])
					{
						for(yp = [-1, 1])
						{
							translate([xp*84/2, yp*142/2, 0])
							difference()
							{
								translate([xp*2, yp*2, 0])
									half_rounded_cube(9, 9, 40, 2.5);
								
								cylinder(d = 3.1, h = 50, center = true, $fn = 30);
							}
						}
					}
					
					for(xp = [-1, 1])
					{
						translate([xp*(84/2+3-1.2), (142/2-2.5), 0])
						rotate(45 + (45+90)*xp, [0, 0, 1])
							edge(2, 50);
					}

				}
			}

			if(twoPart)
			{
				// upper and lower part combining
				translate([0, 17, 0])
				for(xp = [-1, 1])
				{
					translate([xp*(90/2-12), 4/2+10, -18/2-1-7])
					rotate(90, [1, 0, 0])
						cylinder(d = 4, h = 4, center = true, $fn = 30);

					translate([xp*(90/2-12), 20/2, -18/2-1-7])
					rotate(90, [1, 0, 0])
						cylinder(d = 2.2, h = 20, center = true, $fn = 30);

					translate([xp*(90/2-12), 6/2, -18/2-1-7])
					rotate(90, [1, 0, 0])
						cylinder(d = 3.1, h = 6, center = true, $fn = 30);
				}
			}
			
			// USB-C cutout bottom
			translate([0, -140/2, -3.2/2+1-0.3])
			rotate(90, [1, 0, 0])
				half_rounded_cube(9.2+0.3, 3.2+2, 20, 1.2);

			for(xp = [-1, 1])
			{
				// lanyard cutout bottom
				translate([xp*43.8/2, -140/2, -3.2/2+1])
				rotate(90, [1, 0, 0])
					half_rounded_cube(5, 3.2, 20, 1.2);
			}
				
			// USB-C cutout side
			translate([-90/2, 148/2-28, -3.2/2+1-0.3])
			rotate(90, [0, 0, 1])
			rotate(90, [1, 0, 0])
				half_rounded_cube(9.2+0.3, 3.2+2, 20, 1.2);

			// ESP32 antenna cutout
			translate([90/2-1, 148/2-48.7, -3.2/2+2])
			rotate(90, [0, 0, 1])
			rotate(90, [1, 0, 0])
				half_rounded_cube(19, 3.2, 3, 0.3);

			// side button cutout
			translate([90/2, 148/2-29.35, -3.2/2+2])
			rotate(90, [0, 0, 1])
			rotate(90, [1, 0, 0])
				half_rounded_cube(5.7, 3.2, 20, 0.3);

			// SMA cutout
			translate([90/2, 148/2-13, -12/2+1])
			rotate(90, [0, 0, 1])
			rotate(90, [1, 0, 0])
				half_rounded_cube(8.3, 12, 20, 0.3);
			
			// top expansion cutout
			translate([-90/2+18.3+(8*2.54)/2, 140/2, -2.54/2+1-0.2])
			rotate(90, [1, 0, 0])
				half_rounded_cube(8*2.54+1, 2.54+2, 20, 0.1);

			translate([90/2-18.4-(10*2.54)/2, 140/2, -2.54/2+1-0.2])
			rotate(90, [1, 0, 0])
				half_rounded_cube(10*2.54+1, 2.54+2, 20, 0.1);
		}
	}
}

difference()
{
	union()
	{
		color("#00cccc")
		case(true);

		if(true)
		{
			//color("#333333")
			translate([-90/2, 148/2, 0])
				%import("badgeCarrierCard.stl");

			translate([-90/2+12, 148/2-103, -18/2-1])
			rotate(90, [1, 0, 0])
				%cylinder(d = 18, h = 65, center = true, $fn = 50);

			translate([90/2-12, 148/2-103, -18/2-1])
			rotate(90, [1, 0, 0])
				%cylinder(d = 18, h = 65, center = true, $fn = 50);
		}
	}
	union()
	{
		// angular cut for inspection
		if(false)
		{
			rotate(60, [0, 0, 1])
			translate([0, -100, 0])
				cube([200, 200, 200], center = true);
		}
		// top only
		if(false)
		{
			translate([0, -100+23, 0])
				cube([200, 200, 200], center = true);
		}
		// bottom only
		if(false)
		{
			translate([0, +100+23, 0])
				cube([200, 200, 200], center = true);
		}
	}
}
