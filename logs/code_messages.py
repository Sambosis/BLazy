
import math

# OpenSCAD Utilities

# ----------------------
# Common Parameters
# ----------------------

# Default layer height for 3D printing
layer_height = 0.2;  // mm

# Default print tolerance for 3D printing
print_tolerance = 0.2; // mm

# Minimum wall thickness for structural integrity
min_wall_thickness = 0.8; // mm

# ----------------------
# Clearance Calculation Functions
# ----------------------

# Function to calculate clearance between two parts
# Usage:
#   clearance(10, 5)  // returns 5 (10 - 5)
def clearance(part_dimension, mating_dimension):
    return abs(part_dimension - mating_dimension)

# Function to calculate required tolerance for a sliding fit
# Usage:
#   sliding_fit_tolerance(10) // returns 10+0.2
def sliding_fit_tolerance(nominal_dimension):
  return nominal_dimension + print_tolerance;


# ----------------------
# Rounded Corners Module
# ----------------------

# Module for creating rounded corners on a 2D shape 
# Usage:
#   rounded_corner(10, 2) // creates a rounded section in an extrusion
def rounded_corner(radius, segments=32):
    # Create the arc for the rounded section using a circle and cutting a 1/4 portion
    difference(){
       circle(r = radius,$fn=segments);
       translate([-radius,0,0]) square([2 * radius,radius],center = true);
       translate([0, -radius,0]) square([radius, 2 * radius],center = true);
    }


# ----------------------
# Chamfer Module
# ----------------------
# Module for creating a chamfer on a 2D shape
# Usage:
#   chamfer(2,2) // create a 45 degree chamfer where each side is 2mm
def chamfer(size, height):
    polygon(
       points=[
          [0,0],
          [size,0],
          [size, height]
      ]
    );



# ----------------------
# Geometric Utility Functions
# ----------------------

# Function to calculate the hypotenuse of a right triangle
# Usage:
#   hypotenuse(3, 4)  // returns 5
def hypotenuse(side_a, side_b):
  return math.sqrt(side_a**2 + side_b**2)

# Function to calculate the distance between two points in 2D space
def distance_2d(x1, y1, x2, y2):
    dx = x2 - x1;
    dy = y2 - y1;
    return math.sqrt(dx * dx + dy * dy);

# Function to calculate the angle between two vectors
def angle_between_vectors(x1, y1, x2, y2):
  dot_product = x1*x2 + y1*y2;
  magA = math.sqrt(x1*x1 + y1*y1);
  magB = math.sqrt(x2*x2 + y2*y2);
  angle =  math.degrees(math.acos(dot_product / (magA * magB)));
  return angle;


# -----
# Basic Bearing Clearance Helper
# -----

# Calculates clearance for a bearing based on nominal diameter using default tolerance
# Usage:
#  bearing_clearance(10) // returns 10.2mm
def bearing_clearance(nominal_diameter):
  return nominal_diameter + print_tolerance;
   
if __name__ == '__main__':
  # Example usage
  
  echo("Layer Height:", layer_height);
  echo("Print Tolerance:", print_tolerance);
  echo("Min Wall Thickness:", min_wall_thickness);

  echo("Clearance 10-5:", clearance(10, 5));
  echo("Sliding Fit Tolerance 10:", sliding_fit_tolerance(10));

  echo("Hypotenuse 3-4:", hypotenuse(3, 4));

  echo("Bearing Clearance 10mm:", bearing_clearance(10));

  // Example rounded corner:
  linear_extrude(height = 10)
    difference(){
      square(15);
      translate([0,0]) rounded_corner(5);
      translate([15,15]) rotate(a=180) rounded_corner(5);
      translate([0, 15]) rotate(a=90) rounded_corner(5);
      translate([15, 0]) rotate(a=270) rounded_corner(5);

    }
    
    // Example Chamfer
  linear_extrude(height = 10, center=true)
  translate([25, 0,0]) difference(){
    square(15);
    translate([-7.5,7.5,0]) rotate(a=45) chamfer(5,5);
    translate([7.5,-7.5, 0]) rotate(a=225) chamfer(5,5);
    translate([7.5, 7.5,0]) rotate(a=135) chamfer(5,5);
    translate([-7.5, -7.5, 0]) rotate(a=-45) chamfer(5,5);

  }
  
  
  
  }

```

# filepath: C:\mygit\BLazy\repo\scad\bearings.scad
include <utils.scad>

// -----------------------------------------------
// Helper Functions for Bearing Calculations
// -----------------------------------------------

// Calculate maximum ball size based on bearing diameters
function max_ball_size(outer_diameter, inner_diameter) =
    (outer_diameter - inner_diameter) / 2;


// Calculate the number of balls based on circumference and ball size
function optimal_num_balls(outer_diameter, inner_diameter, ball_diameter) =
    let
      circumference = (inner_diameter + (ball_diameter)) * PI,
      min_ball_spacing = ball_diameter
    in
     (circumference/ (ball_diameter  + print_tolerance));


// Function to calculate the radial clearance for bearings
function bearing_radial_clearance(nominal_diameter) =
    print_tolerance;



// -----------------------------------------------
// Ball Bearing Module
// -----------------------------------------------

module ball_bearing(outer_diameter, inner_diameter, num_balls = 0, ball_diameter_override = 0, height = 5) {
  
    // Calculate ball size, use override if provided. If not calculate automatically
    ball_diameter = ball_diameter_override > 0 ? ball_diameter_override : max_ball_size(outer_diameter, inner_diameter) - bearing_radial_clearance(outer_diameter) ;
    
    // Calculate number of balls if 0 was passed in
    num_balls = num_balls == 0? optimal_num_balls(outer_diameter, inner_diameter, ball_diameter) : num_balls;


    // Calculate the pitch diameter
    pitch_diameter = (inner_diameter + outer_diameter) / 2;

   
    
    // Create outer race
    difference(){
      cylinder(h = height, r = outer_diameter/2, $fn=100);
     
     // Create inner race
      cylinder(h= height+1, r= inner_diameter/2, $fn=100);
       
       //create ball race cut
       for(i=[0:num_balls-1]){
         rotate(a=i * 360/num_balls){
              translate([pitch_diameter/2,0,height/2])
         rotate([-90,0,0])
        cylinder(h = ball_diameter, r = ball_diameter/2 + bearing_radial_clearance(pitch_diameter), $fn=20);

          }
        }
    }
    
      // Create balls
      for(i=[0:num_balls-1]){
        rotate(a=i * 360/num_balls){
          translate([pitch_diameter/2,0,height/2])
          sphere(r=ball_diameter/2, $fn=20);
        }
      }


}

// -----------------------------------------------
// Roller Bearing Module
// -----------------------------------------------
module roller_bearing(outer_diameter, inner_diameter, num_rollers = 0, roller_diameter_override=0, roller_height= 5){

    // Calculate roller size based on max
    roller_diameter =  roller_diameter_override > 0 ? roller_diameter_override : max_ball_size(outer_diameter, inner_diameter) - bearing_radial_clearance(outer_diameter);

   // Calculate number of balls if 0 was passed in
    num_rollers = num_rollers == 0? optimal_num_balls(outer_diameter, inner_diameter, roller_diameter) : num_rollers;


    
   // Calculate pitch diameter
     pitch_diameter = (inner_diameter + outer_diameter) / 2;

    // Outer race
    difference(){
      cylinder(h= roller_height, r= outer_diameter/2, $fn=100);
       // Inner race
      cylinder(h= roller_height + 1, r= inner_diameter/2, $fn=100);
       
        // Create roller race cut
         for(i=[0:num_rollers-1]){
            rotate(a=i * 360/num_rollers){
                translate([pitch_diameter/2,0,roller_height/2])
                  rotate([-90,0,0])
                cylinder(r=roller_diameter/2 + bearing_radial_clearance(pitch_diameter), h= roller_height/2 + bearing_radial_clearance(pitch_diameter) , $fn=20);


                }

         
          }
      }


     // Create Rollers
     for(i=[0:num_rollers-1]){
        rotate(a=i * 360/num_rollers){
             translate([pitch_diameter/2,0,roller_height/2])
                  rotate([-90,0,0])
              cylinder(r=roller_diameter/2, h= roller_height/2, $fn = 20);
          }
      }

}


// -------------------------------------------------
// Usage Examples
// -------------------------------------------------
if (__name__ == "__main__") {

  // Example of ball bearing with automatic ball size and number of balls
  ball_bearing(outer_diameter=30, inner_diameter=10, height= 10);
  
  // Example of ball bearing with specified ball diameter and number of balls
  translate([50,0,0])
  ball_bearing(outer_diameter=20, inner_diameter=10, num_balls = 10, ball_diameter_override = 3, height= 10);

  // Example Roller bearing
  translate([0, 50, 0])
    roller_bearing(outer_diameter = 30, inner_diameter = 10, height=10);


  // Example Roller bearing with specified number of rollers and diameter
   translate([50,50,0])
   roller_bearing(outer_diameter = 20, inner_diameter=10 , num_rollers = 10, roller_diameter_override= 1.75, height=10);

  
}

# filepath: C:\mygit\BLazy\repo\scad\tolerance_test.scad

include <utils.scad>
include <bearings.scad>
//include <joints.scad>
//include <gears.scad>


//-----
// Tolerance Test Grid
//-----
module tolerance_test_grid(test_size = 10){
    module clearance_test(clearance_value){
        difference(){
            cube(test_size);
            translate([test_size/2,test_size/2,test_size])
            cube([test_size-(clearance_value*2), test_size-(clearance_value*2),test_size+2], center=true);
        }
    }


    module bearing_test(outer_diameter, inner_diameter){
         ball_bearing(outer_diameter=outer_diameter, inner_diameter=inner_diameter, height =test_size) ;

        }

    module joint_test(){
         // Placeholder for joint test module
         echo("joint_test placeholder");
         cube(test_size);
     }


    module gear_test(){
        //placeholder for gear test module
          echo("gear_test placeholder");
         cube(test_size);
    }

    // Layout grid
    x_offset = 0;
    y_offset = 0;
    row_height = test_size *3 ;
    col_width = test_size* 3;
    
    // Clearances Tests
    translate([x_offset, y_offset, 0]){
        linear_extrude(height=test_size)
        clearance_test(0.1);
    }
     
      translate([x_offset+col_width, y_offset, 0]){
           linear_extrude(height=test_size)
          clearance_test(0.2);    
      }

        translate([x_offset+ col_width*2, y_offset, 0]){
              linear_extrude(height=test_size)
            clearance_test(0.3);
        }
   
   translate([x_offset, y_offset + row_height, 0]){
      linear_extrude(height=test_size)
        clearance_test(0.4);
    }
    

    // Bearing Tests
    translate([x_offset ,y_offset + row_height*2, 0]){
       linear_extrude(height=test_size)
    bearing_test(15,5);
    }
     translate([x_offset +col_width,y_offset + row_height*2, 0]){
          linear_extrude(height=test_size)
       bearing_test(30,10);
      }

   translate([x_offset +col_width*2,y_offset + row_height*2, 0]){
       linear_extrude(height=test_size)
    bearing_test(50,15);
    }

    // Joint Tests
     translate([x_offset, y_offset +row_height*3,0]){
         joint_test();
    }
      translate([x_offset+ col_width, y_offset +row_height*3,0]){
         joint_test();
    }
       translate([x_offset+ col_width*2, y_offset +row_height*3,0]){
         joint_test();
    }


    // Gear Tests
    translate([x_offset, y_offset + row_height*4,0]){
       gear_test();        
    }
      translate([x_offset + col_width, y_offset+ row_height*4,0]){
           gear_test();
    }
     translate([x_offset + col_width*2, y_offset+ row_height*4,0]){
         gear_test();
    }


}


//-----
// Individual Test Modules
//-----

// Bearing Rotation Test
module bearing_rotation_test(outer_diameter = 30, inner_diameter =10, height= 20) {
 // Creates an outer housing and inner ring allowing the internal bearing to rotate
     difference(){
        cylinder(h = height+2, r = outer_diameter/2 + print_tolerance, $fn=100);
         cylinder(h= height+3, r= inner_diameter/2 - print_tolerance, $fn=100);

    }
    translate([0,0,1]) ball_bearing(outer_diameter=outer_diameter, inner_diameter=inner_diameter, height=height );
}

// Joint Range of Motion Test
module joint_range_test() {
  // Placeholder for joint range of motion test module
  echo("joint_range_test placeholder");
   cube(10);
}


// Gear Mesh Test
module gear_mesh_test(num_teeth_1= 20, num_teeth_2 = 20, height = 10){
    // placeholder for gear mesh test module
      echo("gear_mesh_test placeholder");
          cube(10);
}

// Snap Fit Test
module snap_fit_test(width = 15, height = 5, depth = 10){

     // Placeholder for snap fit
     echo("snap_fit_test placeholder");
     cube([width, depth,height]);
}
// Layer Bridging Test
module layer_bridging_test(width = 20, length = 50, layers=5, layer_height= 0.2) {
    //Test bridging performance over small distance
     linear_extrude(height = layers * layer_height){
        square([width, length], center=true);
       
     }

    translate([0, -30, layers * layer_height]){
        cube([10,5,layers* layer_height], center= true);
    }

     translate([0, 30, layers * layer_height]){
          cube([10,5,layers* layer_height], center = true );
    }
    
}



//-----
// Comprehensive Test Suite
//-----

module comprehensive_test_suite(test_size = 10) {
  // Small bearing test (15mm diameter)
    translate([0,0,0])
    bearing_rotation_test(outer_diameter=15 , inner_diameter= 5, height = 15);
  
  // Medium bearing test (30mm diameter)
   translate([test_size * 10,0,0])
    bearing_rotation_test(outer_diameter=30, inner_diameter=10, height=30);

  // Large bearing test (50mm diameter)
  translate([test_size * 20,0,0])
   bearing_rotation_test(outer_diameter=50, inner_diameter=15, height = 50);

  // All joint types in various sizes
  translate([0,test_size * 10 ,0])
    joint_range_test();
     translate([test_size * 10,test_size* 10,0])
      joint_range_test();
       translate([test_size * 20,test_size* 10,0])
      joint_range_test();
  
  // Gear mesh tests with different tooth counts
     translate([0, test_size * 20 ,0])
    gear_mesh_test(num_teeth_1= 20, num_teeth_2 = 20);
     translate([test_size * 10, test_size * 20,0])
    gear_mesh_test(num_teeth_1= 15, num_teeth_2 = 30);
      translate([test_size * 20, test_size * 20,0])
    gear_mesh_test(num_teeth_1= 30, num_teeth_2 = 15);
  
  // Planetary gear system test
  // Placeholder for planetary gear test module
   translate([0,test_size * 30 ,0]){
   echo("planetary_gear_test placeholder");
     cube(10);
   }
 

  // Worm gear test
  // Placeholder for worm gear test module
   translate([test_size * 10,test_size * 30,0])  {
      echo("worm_gear_test placeholder");
       cube(10);
  }

    // Snap fit tests
     translate([0, test_size * 40 ,0])   snap_fit_test();
      translate([test_size * 10,test_size * 40,0])  snap_fit_test(width=25 , depth=15);
    // Layer bridging tests
     translate([0,  test_size * 50, 0]) layer_bridging_test() ;
     translate([0,  test_size * 60, 0]) layer_bridging_test(width = 40, layers = 10) ;

}





//-----
// Test Parameters
//-----

// Layer height options
layer_height_options = [0.1, 0.2, 0.3];

// Print speed recommendations
print_speed_recommendations = [40, 50, 60]; // mm/s

// Temperature guidelines
temperature_guidelines = [200, 210, 220]; // degrees Celsius

// Retraction settings
retraction_settings = [4, 5, 6];  // mm

// Cooling requirements
cooling_requirements = ["fan_on", "fan_off"];





//-----
// Example Usage
//-----

// Generate tolerance test grid
tolerance_test_grid();

// Generate individual bearing rotation test
translate([100,0,0])
bearing_rotation_test(outer_diameter=25, inner_diameter=8);

// Generate individual snap_fit_test
translate([100, 50 ,0])
snap_fit_test();

// Generate individual layer bridging test
translate([100,100,0])
layer_bridging_test();

// Generate comprehensive test suite
translate([0, 120 ,0])
comprehensive_test_suite();



// -----
// Test result info
// -----

// Test Success Criteria:
// Bearing rotation test = Verify smooth rotation on inner race with minimal wobble and no binding
// Joint range of motion test = Verify full range of motion without excessive play or binding
// Gear mesh test = Verify smooth engagement between gears, no skipping, and proper backlash
// Snap fit test = Verify strong snap connection that is easy to assemble but does not come apart without force
// Layer bridging test = Verify no sagging or stringing on top of the bridged structure and no warping

// Measurement points
// Bearing rotation test = Inner race ID, outer race OD, bearing assembly height, gap between outer and inner ring
// Joint range of motion test = Range of motion in degrees, amount of play in the joint in mm
// Gear mesh test = Center distance between gears, backlash, contact patch size in mm
// Snap fit test= gap between mating features, force to engage and disengage in N,
// Layer bridging test = amount of sagging in mm, deflection between bridge supports


// Troubleshooting guidelines
// If models dont print
    // ensure bed is calibrated
    // Check for excessive warping
    // Reduce print speed
//if tolerances are too tight
    // Increase clearance
    // Reduce extrusion rate
    // Calibrate e-steps and flow
// if tolerances are too loose
    // reduce clearance
    // calibrate estep and flow
// if bridging fails
    // Make sure bed is clean
    // increase cooling
    // decrease bridging length
// if snap fit fails
    // increase the engagement surfaces
    // reduce the size of snap feature
// if prints bind
    // increase clearance
    // check for warping
// if parts break
    // increase wall thickness
    // increase infill
    // adjust printing angles

// Recommended Printer Settings
// Layer height = 0.2mm is a good place to start, can be adjusted based on test results
// Speed = start with 40mm/s. Can be increased for non tolerance parts
// Temperature = 200-220 based on material being used
// Retraction = start with 4-6mm based on material
// Cooling = enable part cooling fan
// Infill = 20-30% should be good

# filepath: C:\mygit\BLazy\repo\scad\fidget_spinner.scad

include <utils.scad>
include <bearings.scad>
//include <joints.scad>  // Placeholder since joints.scad is not provided
//include <gears.scad>  // Placeholder since gears.scad is not provided

// -----------------------------------------------
// Customization Parameters
// -----------------------------------------------

// Overall size
overall_diameter = 80; // mm
center_hub_diameter = 30; // mm
arm_length = 35; // mm
arm_width = 15; // mm
arm_thickness= 8; // mm
weight_diameter = 10; //mm
weight_thickness = 5;
base_layer_thickness = 2;
thumb_pad_height = 3;
thumb_pad_size = 15;
secondary_spinner_size = 10;

// Bearing sizes (608 size compatibility)
center_bearing_outer_diameter = 22;
center_bearing_inner_diameter = 8;
planetary_bearing_outer_diameter = 10;
planetary_bearing_inner_diameter = 3;

// Gear Ratios
sun_gear_teeth = 12;
planet_gear_teeth = 6;
ring_gear_teeth = 24;


// Joint tensions (not used with a joint module, but here for customization)
joint_gap = 0.2; // mm
joint_pin_diameter = 2;  // mm pin for the joint



// Weight distribution (not currently implemented, but here for future expansion)
end_cap_weight = 1;

// Surface Textures (Not implemented with textures, but here for future use)
// Can be implemented using difference of cylinders
thumbpad_texture_depth = 0.2;
thumbpad_texture_spacing =4;


// -----------------------------------------------
// Helper Modules
// -----------------------------------------------

// Placeholder for a gear module
module gear(num_teeth, height, pitch_diameter){

    //Placeholder for gear functionality
    echo("gear placeholder");
     cylinder(h=height, r = pitch_diameter/2);
}

// Placeholder for a joint module
module simple_joint(size){
   echo("simple_joint placeholder,  using default cube");
     cube(size);
}

module thumb_pad(){
    difference(){
       cylinder(h = thumb_pad_height, r = thumb_pad_size/2, $fn=50);
     for (x = [-thumb_pad_size/2 + thumbpad_texture_spacing/2:thumbpad_texture_spacing:thumb_pad_size/2- thumbpad_texture_spacing/2]){
        for(y = [-thumb_pad_size/2 + thumbpad_texture_spacing/2:thumbpad_texture_spacing:thumb_pad_size/2 - thumbpad_texture_spacing/2 ]){
          translate([x,y,0])
           cylinder(h = thumb_pad_height+ thumbpad_texture_depth, r=thumbpad_texture_depth/2,$fn=10);
        }
      }
    }
}


module flip_out_wing(){
     union(){
          rotate([0,0,90]){
                translate([0,0,0])
                difference(){

                  cube([secondary_spinner_size + 2, base_layer_thickness, secondary_spinner_size + 2 ], center= true);
                  translate([0,0,5])
                   cube([secondary_spinner_size , base_layer_thickness +2, secondary_spinner_size], center= true);
                }
                
            
             }
        
          // Ball and socket Placeholder
           translate([0,0,-joint_pin_diameter/2])
          simple_joint(joint_pin_diameter);

          
      }
}



// -----------------------------------------------
// Main Components
// -----------------------------------------------

// Center Hub module
module center_hub() {
  difference() {
    cylinder(h = arm_thickness+base_layer_thickness, r = center_hub_diameter/2, $fn = 50);
     cylinder(h= arm_thickness+base_layer_thickness+1, r= center_bearing_inner_diameter/2, $fn =50);
  }
  translate([0,0,base_layer_thickness])
  ball_bearing(outer_diameter = center_bearing_outer_diameter, inner_diameter = center_bearing_inner_diameter, height=arm_thickness);
  
}


// Arm module including planetary gear system and flip-out wings
module arm() {
    linear_extrude(height= arm_thickness)
    difference(){
        translate([0,0,0])
        rounded_corner(arm_width/2);
        translate([arm_length,0])
        rotate(a=180)rounded_corner(arm_width/2);
      }
    translate([arm_length/2, 0, base_layer_thickness+arm_thickness/2 +thumb_pad_height/2+1])
    rotate([0,0,90])
    thumb_pad();
      
       // Planetary Gear System
   translate([arm_length/2 - arm_width/1.5,0, arm_thickness/2  +base_layer_thickness])
    rotate([0,0,90])    
    difference(){
        cylinder(h = arm_thickness, r= planetary_bearing_outer_diameter / 2 +3, $fn = 50);
         cylinder(h = arm_thickness+1, r= planetary_bearing_inner_diameter / 2 - print_tolerance , $fn=50);
      }
       translate([arm_length/2 - arm_width/1.5,0, base_layer_thickness ])
    ball_bearing(outer_diameter=planetary_bearing_outer_diameter, inner_diameter = planetary_bearing_inner_diameter, height= arm_thickness, $fn=30);

        translate([arm_length/2 - arm_width/1.5,0, base_layer_thickness+arm_thickness/2+ print_tolerance])
         gear(num_teeth=sun_gear_teeth, height= 5, pitch_diameter = (planetary_bearing_outer_diameter));

         for(i=[0:2]){
                rotate(a= i * 360/3){
             translate([arm_length/2 - arm_width/1.5 + ((planetary_bearing_outer_diameter/2 +2) * 1.5) , 0, base_layer_thickness+arm_thickness/2 - print_tolerance])
            gear(num_teeth= planet_gear_teeth, height = 5, pitch_diameter= (planetary_bearing_outer_diameter/2));

            //Additional planet gears
             translate([arm_length/2 - arm_width/1.5 + ((planetary_bearing_outer_diameter/2 +2) * 1.5) , 0,  base_layer_thickness+arm_thickness/2 + print_tolerance])
                ball_bearing(outer_diameter = planetary_bearing_outer_diameter/2 , inner_diameter=planetary_bearing_inner_diameter ,height = arm_thickness);
            
            }
        }
       translate([arm_length/2 - arm_width/1.5,0, base_layer_thickness+arm_thickness/2+print_tolerance])
        gear(num_teeth=ring_gear_teeth, height = 5, pitch_diameter = (planetary_bearing_outer_diameter + (planetary_bearing_outer_diameter/2 + 2)*2));

     //Flip out wings
     translate([arm_length, 0 ,base_layer_thickness+ arm_thickness/2])
      flip_out_wing();
     
    // Integrated Weight at end of arms
        translate([arm_length+ secondary_spinner_size/2,0, base_layer_thickness+arm_thickness/2])
       cylinder(h= weight_thickness, r = weight_diameter/2, $fn=30);
}


// -----------------------------------------------
// Assembly Instructions (comments in the code)
// -----------------------------------------------
/*
  Assembly Instructions:

    1. Print all parts in the orientation suggested in the print settings.
    2. No support material should be needed.
    3. The Center bearing, and the planetary gears/bearings need to print in place
    4. The flip_out wings are printed as a single piece including the ball joint

  Print Orientation Guidelines:
    1. Main body flat on the print bed for maximum strength for the base layer
    2. Parts will not shift with good bed adhesion
    3. Print at a medium speed for best results
    
  Post-Processing Tips:
    1. Ensure no plastic debris is near any moving parts
    2. If tolerances are too tight you will need to use a small file
    3. If parts are to loose use a thin  glue to thicken parts as needed

*/

// -----------------------------------------------
// Main Fidget Spinner Module
// -----------------------------------------------
module fidget_spinner() {
  center_hub();

  for (i = [0:2]) {
    rotate(a = i * 360 / 3) {
      translate([center_hub_diameter/2 + arm_length/2, 0, 0])
      arm();
    }
  }
}

// -----------------------------------------------
// Example Configurations
// -----------------------------------------------
if (__name__ == "__main__") {

  // Basic spinner setup
  fidget_spinner();

  // Optional gear train version (if gears.scad was implemented)
  // Placeholder for implementation of optional gear train
  translate([100,0,0]){
        echo("Placeholder for gear train fidget spinner");
       fidget_spinner();
  }
  

  // Alternative arm designs (future implementation)
  translate([0,100,0]){
    echo("Placeholder for alternative arm design");
    fidget_spinner();
  }


  // Different size options (Adjust parameters above)
translate([100,100,0]){
    echo("Placeholder for alternative size design");
    fidget_spinner();
  }
  

  // Various weight configurations (Adjust parameters above)
    translate([0,200,0]){
         echo("Placeholder for different weights");
        fidget_spinner();
    }
}

// -----------------------------------------------
// Additional Comments
// -----------------------------------------------
/*
  Print Settings Recommendations:
    Layer Height: start with 0.2mm (adjust for details)
    Infill: 20-30% (adjust for weight)
    Speed: 40-50 mm/s (adjust based on printer)
    Temperature: based on material guidelines
    Support: None

   Assembly Tips:
     1. No assembly should be required for this print
     2. if you have difficulty spinning its likely due to tolerances, some sanding maybe required

  How to Customize the Design:

    1. Adjust parameters at the top of the file for different sizes, weights and ratios
    2. Add text or embossed logos on the thumb pad
    3. Change the number of arms by changing the for loop
    4. Experiment with different gear ratios if gears.scad was implemented
    5. Remove the flip_out wings as an option
    6. Add a different feature to the end of the arm such as a bottle opener
    7. Experiment with different textured patterns for surfaces
    8. Combine the individual test objects into this document for ease of adjustments

 Troubleshooting Common Issues:
   1. If bearings bind, increase clearances in the "utils.scad" file
   2. If parts break, review the strength of your print settings and consider printing at a higher infill.
   3. If gears skip, adjust teeth count in gear module and recalculate for additional space
  
 Maintenance Suggestions:
  1.  Avoid oils and grease. These may degrade the plastic and attract dust
  2.  If bearings become stiff, remove any debris by using a tooth brush
  3. store away from direct sunlight to avoid warping
*/

# filepath: C:\mygit\BLazy\repo\scad\bearings.scad
include <utils.scad>

// -----------------------------------------------
// Helper Functions for Bearing Calculations
// -----------------------------------------------

// Calculate maximum ball/roller size based on bearing diameters
function max_ball_size(outer_diameter, inner_diameter) =
    (outer_diameter - inner_diameter) / 2;


// Calculate the optimal number of balls/rollers based on circumference, ball size and tolerance
function optimal_num_balls(outer_diameter, inner_diameter, ball_diameter) =
    let
      circumference = (inner_diameter + ball_diameter) * PI, // Approximate pitch circumference
      min_ball_spacing = ball_diameter + print_tolerance // Minimum space between balls

    in
     (circumference / min_ball_spacing); 


// Function to calculate the radial clearance for bearings. Uses the global print_tolerance from utils.scad
function bearing_radial_clearance(nominal_diameter) =
    print_tolerance;


// Function to calculate race groove radius. Uses the global print_tolerance from utils.scad. Provides a 10% larger diameter then the ball
function race_groove_radius(ball_diameter) =
   (ball_diameter/2) + print_tolerance * 1.2; 
    
// Calculate the depth for the race groove cut based on the ball radius. Provides a 10% larger diameter then the ball + .1mm for clearance
function race_groove_depth(ball_diameter) =
    (ball_diameter/2) + print_tolerance + .1;






// -----------------------------------------------
// Ball Bearing Module
// -----------------------------------------------

module ball_bearing(outer_diameter, inner_diameter, height = 5, num_balls = 0, ball_diameter_override = 0,  with_flange = false, flange_height = 2, flange_thickness = 2, mounting_holes = false, mounting_hole_diameter = 4, mounting_hole_spacing = 2) {
    
     // Calculate ball size, use override if provided. If not calculate automatically
    ball_diameter = ball_diameter_override > 0 ? ball_diameter_override : max_ball_size(outer_diameter, inner_diameter) - bearing_radial_clearance(outer_diameter) ;
    
    // Calculate number of balls if 0 was passed in
    num_balls = num_balls == 0? optimal_num_balls(outer_diameter, inner_diameter, ball_diameter) : num_balls;

    // Calculate the pitch diameter
    pitch_diameter = (inner_diameter + outer_diameter) / 2;
    
    // Calculate the race groove radius
    groove_radius = race_groove_radius(ball_diameter);

      
    // Main bearing structure with optional flange
    difference(){
        
         union(){
        //Outer Diameter
            cylinder(h = height, r = outer_diameter/2, $fn=100);
           
            //Optional flange
              if (with_flange){
                  translate([0,0,height]){
                    cylinder(h = flange_height, r = outer_diameter/2+flange_thickness, $fn=100);
                    }
                   translate([0,  0, -flange_height]){
                    cylinder(h = flange_height, r = outer_diameter/2+flange_thickness, $fn=100);
                     }
                }    
           
        }

         //Inner Diamter
          cylinder(h = height +1 , r = inner_diameter/2, $fn = 100);
         
        // Cut the race grooves into the inner and outer races. 
          for(i=[0:num_balls-1]){
             rotate(a=i * 360/num_balls){
                translate([pitch_diameter/2,0,height/2])
              rotate([-90,0,0])
                
                // Create the groove cut profile
                  intersection(){
                   // Cylinder to trim intersection curve with
                   cylinder(h = ball_diameter * 2, r = groove_radius ,$fn=20);

                   //Box to simulate curve cutting
                    translate([0, -groove_radius,0])
                     cube([ball_diameter/1.5, groove_radius * 2, ball_diameter * 1.5 ], center=true);
                             }
              
              }
          }
       
        
    }
     // Create the mounting holes on optional flange if needed
      if(with_flange && mounting_holes){
          for(i=[0:3]){
            rotate(a = i * 90){
                translate([outer_diameter/2 + flange_thickness + mounting_hole_spacing,0, height+flange_height/2])
                    rotate([0,90,0])
                cylinder(r = mounting_hole_diameter/2, h = flange_height+1, $fn=20);
                 translate([outer_diameter/2 + flange_thickness + mounting_hole_spacing,0, -flange_height/2])
                    rotate([0,90,0])
                cylinder(r = mounting_hole_diameter/2, h = flange_height+1, $fn=20);
                 }
             }
      }



    // Create the balls inside the race groove (not for printing just for visualization)
        for(i=[0:num_balls-1]){
             rotate(a=i * 360/num_balls){
                translate([pitch_diameter/2,0,height/2])
                   sphere(r=ball_diameter/2, $fn=20);
            }
      }
}

// -----------------------------------------------
// Roller Bearing Module
// -----------------------------------------------
module roller_bearing(outer_diameter, inner_diameter, height = 5, num_rollers = 0, roller_diameter_override=0, roller_height_override = 0, tapered_rollers = false, with_cage = false, cage_thickness=1) {
  
    // Calculate roller size based on max
    roller_diameter =  roller_diameter_override > 0 ? roller_diameter_override : max_ball_size(outer_diameter, inner_diameter) - bearing_radial_clearance(outer_diameter);

    //Calculate the roller height if not overridden
    roller_height = roller_height_override > 0 ? roller_height_override : height/2 ;

   // Calculate number of rollers if 0 was passed in
    num_rollers = num_rollers == 0? optimal_num_balls(outer_diameter, inner_diameter, roller_diameter) : num_rollers;
    
    // Calculate pitch diameter
    pitch_diameter = (inner_diameter + outer_diameter) / 2;

    // Calculate race groove radius
    groove_radius = race_groove_radius(roller_diameter);

    // Main roller bearing structure
    difference(){
        // Outer race
            cylinder(h = height, r = outer_diameter/2, $fn=100);

         // Inner race
            cylinder(h = height+1, r = inner_diameter/2, $fn = 100);
      
         // Cut the race grooves into the inner and outer races
        for(i=[0:num_rollers-1]){
            rotate(a=i * 360/num_rollers){
              translate([pitch_diameter/2,0,height/2])
                rotate([-90,0,0])
         
                intersection(){
                   // Cylinder to trim intersection curve with
                   cylinder(h = roller_diameter * 2, r = groove_radius ,$fn=20);

                   //Box to simulate curve cutting
                    translate([0, -groove_radius,0])
                     cube([roller_diameter/1.5, groove_radius * 2, roller_diameter * 2], center=true);
                }


              }
        }

    }


    // Create Rollers
      for(i=[0:num_rollers-1]){
        rotate(a = i * 360 / num_rollers){
             translate([pitch_diameter/2,0,height/2])
             rotate([-90,0,0]) 
             if (tapered_rollers) {
              // implement a tapered roller if needed
              rotate([-45,0,0])
              cylinder(r1 = roller_diameter/2, r2 = roller_diameter/2 - (roller_diameter/4), h= roller_height +print_tolerance ,$fn= 20);
            
             } else {
              // Standard cylinder roller
               cylinder(r=roller_diameter/2, h= roller_height, $fn = 20);
            }
            
          }
      }
     
      //Optional Seperator Cage
      if(with_cage){
                  for(i=[0:num_rollers-1]){
                        rotate(a=i * 360/num_rollers){
                                translate([pitch_diameter/2,0,height/2])
                                rotate([-90,0,0])
                                 cylinder(r= roller_diameter/2 + cage_thickness, h= roller_height+ bearing_radial_clearance(outer_diameter), $fn= 20);
                            }
                  }

                   for(i=[0:num_rollers-1]){
                        rotate(a=i * 360/num_rollers){
                                translate([pitch_diameter/2,0,height/2])
                        rotate([-90,0,0])
                       cylinder(r= roller_diameter/2 , h= roller_height , $fn= 20, center=true);
                            }
                  }
            }

}



// -------------------------------------------------
// Usage Examples
// -------------------------------------------------
if (__name__ == "__main__") {

  // Example of ball bearing without features
  ball_bearing(outer_diameter=30, inner_diameter=10, height= 10);
  
  // Example of ball bearing with flange and mountinig holes
 translate([40,0,0])
	 ball_bearing(outer_diameter=30, inner_diameter=10, height = 10, with_flange = true, mounting_holes = true);

  // Example of ball bearing with specified ball diameter and number of balls
  translate([0,40,0])
	ball_bearing(outer_diameter=20, inner_diameter=10, num_balls = 10, ball_diameter_override = 3, height= 10);

  // Example Roller bearing
  translate([40, 40, 0])
    roller_bearing(outer_diameter = 30, inner_diameter = 10, height=10);


    // Example Tapered Roller bearing
     translate([0, 80,0])
    roller_bearing(outer_diameter = 30, inner_diameter = 10, height=10, tapered_rollers= true,  num_rollers=13);


  // Example Roller bearing with specified number of rollers, diameter and cage
   translate([40,80,0])
   roller_bearing(outer_diameter = 20, inner_diameter=10 , num_rollers = 10, roller_diameter_override= 1.75, height=10, with_cage =true);

  
}

# filepath: C:\mygit\BLazy\repo\scad\joints.scad
include <utils.scad>

// Configuration Constants
$fn = 50; // Default smoothness for circles
MIN_WALL = 0.8; // Minimum wall thickness for structural integrity

// Helper function to calculate clearance
function get_clearance(dimension) = dimension + print_tolerance;
function get_snap_clearance(size) = size + print_tolerance * 2;

// -----
// Enhanced Hinge Joint Module
// -----
module enhanced_hinge(
    width = 20,           // Total width of the hinge
    length = 30,          // Length of hinge knuckles
    thickness = 6,        // Thickness of the hinge
    pin_diameter = 4,     // Diameter of the hinge pin
    knuckle_count = 7,    // Number of knuckles in the hinge (must be an odd number)
    stop_angle = 180,       // Maximum opening angle in degrees (can be set limit range of motion)
    has_detents = false,  // True to include detent positions
    detent_angles = [0, 90, 180], // List of detent angles (only if has_detents is true)
    tolerance_multiplier = 1.0 //Multiplier for all tolerances. A value greater then 1 will increase the total tolerance
) {
    
    //Check if the number of knuckles is an odd number
    if (knuckle_count % 2 == 0) {
       echo("Error: knuckle_count must be an odd number, reconfiguring to an odd number"); 
       knuckle_count = knuckle_count + 1;
    }

    // Calculate intermediate parameters
    knuckle_width = width / knuckle_count;
    pin_radius = pin_diameter / 2;

    // Main body of the hinge
    difference()
    {   
        union(){
             // Hinge Body
              cube([width, length, thickness], center = false);
           
            // Hinge Knuckles
            for (i = [0:knuckle_count - 1])
               { 
               translate([i * knuckle_width, 0, 0])
                cube([ knuckle_width, length, thickness  ], center = false);
               }
        }
          
          // Create pin hole
          for (i = [0:knuckle_count - 1]) {

          translate([i * knuckle_width + knuckle_width/2, length/2, thickness/2]) 
             rotate([90,0,0])
           cylinder(h = length + 2, r = (pin_radius * tolerance_multiplier) +print_tolerance , $fn=20);
            
             }
            
           // Cutout if a stop angle is provided
            if(stop_angle < 180){
                translate([width/2, length/2 ,thickness/2])
                     rotate([0,0, stop_angle/2 -90  ])
                      cube([length+2, length+2, thickness+1],center=true);
                    translate([width/2, length/2 ,thickness/2])
                    rotate([0,0,-stop_angle/2 +90])
                   cube([length +2, length +2, thickness+1], center=true); 
            }

           if(has_detents){
               for(angle = detent_angles){
                    translate([width/2, length/2 ,thickness/2])
                        rotate([0,0,angle-90])
                     translate([length/2, 0, -print_tolerance /2])
                            rotate([90,0,0])
                         cylinder(h=pin_radius , r = pin_radius/2 , $fn = 10); 
               
               }
           }
    }      

    // Create the Pin
    translate([0, length/2, thickness/2])
     rotate([90,0,0])
    cylinder(h= length , r = pin_radius , $fn=20);
           
     // Detents on the pin
   if (has_detents){
     for(angle = detent_angles){

    translate([width/2, length/2 ,thickness/2])
        rotate([0,0,angle-90])
      translate([0,0,-thickness/2]) 
        rotate([90,0,0])
        cylinder(h=length, r= pin_radius/2, $fn= 10 );

  
       }

    }
}


//-----
// Ball and Socket Joint Module
//-----
module ball_socket_joint(
    ball_diameter = 10,     // Diameter of the ball
    socket_thickness = 2,   // Thickness of the socket wall
    retention_lip = 0.5,    // Lip height for retention
    max_angle = 45,         // Maximum articulation angle in degrees

    tolerance_multiplier = 1.0 //Multiplier for all tolerances. A value greater then 1 will increase the total tolerance
) {
   
    // Calculate parameters
     ball_radius = ball_diameter / 2;
     socket_radius = ball_radius + socket_thickness;
    
    difference() {
        union() {
            // Socket exterior
           sphere(r = socket_radius, $fn=50);
          
        }

        // Socket interior (cutout for the ball)
            translate([0,0,-ball_radius-retention_lip*tolerance_multiplier])
            sphere(r = ball_radius * tolerance_multiplier , $fn=50);
            
        // Cut limit for the rotation of the joint
         if (max_angle < 180){
         translate([0, 0, -ball_radius/2])
           rotate([-max_angle/2 ,0,0])
            cube([socket_radius * 2, socket_radius * 2 ,ball_radius], center= true);
        translate([0, 0,  -ball_radius/2])
          rotate([max_angle/2, 0,0])
           cube([socket_radius * 2, socket_radius * 2 , ball_radius], center=true);
         
        
            translate([0,0,-ball_radius/2])
         rotate([0,-max_angle/2,0])
            cube([socket_radius * 2, socket_radius * 2 ,ball_radius], center= true);
         
          translate([0,0,-ball_radius/2])
         rotate([0,max_angle/2,0])
            cube([socket_radius * 2, socket_radius * 2 , ball_radius], center=true);
          
             translate([0,0,-ball_radius/2])
            rotate([0,0,max_angle/2])
             cube([socket_radius*2, socket_radius*2, ball_radius], center=true);

            translate([0,0,-ball_radius/2])
            rotate([0,0,-max_angle/2])
         cube([socket_radius*2, socket_radius*2,ball_radius], center=true);
         }


     }
      // Build the ball.
    translate([0,0,-ball_radius/2-retention_lip])
       sphere(r= ball_radius, $fn=50);
}



//-----
// Living Hinge Module
//-----
module living_hinge(
    width = 30,          // Total width of the hinge
    length = 50,         // Total length of the hinge
    thickness = 2,       // Thickness of the hinge (important for flexibility)
    pattern_width = 4,   // Width of each flexible element
    pattern_spacing = 2, // Space between flexible elements
    pattern_depth = 0.5, // Depth of the pattern cut from the surface
      direction = "vertical", // Set the direction of flex of the hinge
    tolerance_multiplier = 1.0 //Multiplier for all tolerances. A value greater then 1 will increase the total tolerance
) {
    //Validate direction string
    if(direction != "vertical" && direction != "horizontal"){
          echo("ERROR: direction must = 'horizontal' or 'vertical', using default of 'vertical'");
         direction = "vertical";
    }

     // Check for pattern width to large, this may cause problems and or the pattern to be skipped.
     if (pattern_width > width || pattern_width > length) {
        echo("ERROR: Pattern width is larger then width or length, please reduce pattern width.");
    }
    
     // Handle very small pattern spacing for printability concerns
     if (pattern_spacing < print_tolerance){
        echo("ERROR: Pattern spacing is too small, increasing spacing");
         pattern_spacing = print_tolerance + 0.1;
    }

    if(direction == "horizontal"){   
        linear_extrude(height = thickness)
            for(x = [pattern_spacing/2: pattern_width + pattern_spacing : width - pattern_spacing/2 ]){
            translate([x,0,0])
                  difference(){
                        square([pattern_width , length], center = true);
                        translate([0,0, pattern_depth * tolerance_multiplier])
                            square([pattern_width, length - (pattern_spacing)], center = true);
                     }
             }
    }

  if(direction == "vertical"){
        linear_extrude(height = thickness)
            for(y = [pattern_spacing/2 : pattern_width + pattern_spacing : length - pattern_spacing/2]){
                translate([0,y,0])
                      difference(){
                         square([width  , pattern_width ], center = true);   
                         translate([0,0, pattern_depth * tolerance_multiplier])
                        square([width - (pattern_spacing) , pattern_width ], center = true);
                        
                        }
                 }
        }
}



//-----
// Snap Fit Joint Module
//-----
module snap_fit_joint(
    width = 20,           // Width of the base part
    height = 5,           // Height of the base part
    depth = 10,           // Depth of the base part or section
    snap_type = "hook",  // Type of snap fit ("hook", "barb", "dovetail")
    snap_size = 4,        // Size of the snap feature
    snap_depth = 0.8,     // Depth of the snap feature
    gap_size = 0.2,    // space betwen parts
       mating_clearance = true, // Should this be a mating fit?
       tolerance_multiplier = 1.0 //Multiplier for all tolerances. A value greater then 1 will increase the total tolerance
) {
      // Validate snap_type string
        if (snap_type != "hook" && snap_type != "barb" && snap_type != "dovetail"){
            echo("ERROR: snap_type must be 'hook', 'barb', or 'dovetail', using default of hook type.");
             snap_type = "hook";
        }
    
   if(mating_clearance){
     clearance =  gap_size + print_tolerance * 2;
    } else {
      clearance = gap_size;
    }

    module snap_hook(snap_size, snap_depth){
           translate([0,0,0])
            polygon(
            points=[
                    [0,0],
                    [snap_size/2,snap_depth/2],
                       [snap_size/2,snap_depth  * tolerance_multiplier],
                    [0,snap_depth * tolerance_multiplier ],
                 
                  ]
            );
    }

    module snap_barb(snap_size, snap_depth){
            translate([0,0,0])
            polygon(
            points=[
                [0,0],
                  [snap_size/2,snap_depth /2 * tolerance_multiplier],
                  [snap_size/2, snap_depth  * tolerance_multiplier],
                  [0, snap_depth * tolerance_multiplier],
                 
                  ]
            );
    }

     module snap_dovetail(snap_size, snap_depth){
             translate([0,0,0])
        polygon(
            points=[
                [0,0],
                [snap_size/2,snap_depth/2],
                [snap_size,0],
                 [snap_size,snap_depth * tolerance_multiplier],
                [0,snap_depth * tolerance_multiplier]

            ]
        );
    }


    difference(){
            // Base Body
          cube([width,  depth, height  ], center = false);
        
       translate([0,depth/2,height])
              if(snap_type == "hook"){
                   linear_extrude(height = snap_size/2)
                    snap_hook(snap_size, snap_depth);
              }
             if(snap_type == "barb"){
                   linear_extrude(height = snap_size/2)
                   snap_barb(snap_size, snap_depth);

              }

            if(snap_type == "dovetail"){
               rotate([0,0,180])
                   linear_extrude(height = snap_size/2)
                   snap_dovetail(snap_size, snap_depth);       
             }

	}
    translate([0,depth,0])
    difference(){
        cube([width, depth/1.5, height + clearance  ], center=false);

        translate([0,depth/1.5/2,height ])
         if(snap_type == "hook"){
                   linear_extrude(height = snap_size/2)
                    snap_hook(snap_size, snap_depth);
              }
             if(snap_type == "barb"){
                   linear_extrude(height = snap_size/2)
                   snap_barb(snap_size, snap_depth);
              }

            if(snap_type == "dovetail"){
               rotate([0,0,180])
                   linear_extrude(height = snap_size/2)
                   snap_dovetail(snap_size, snap_depth);       
             }
}
}

// -----
// Example Usage
// -----

if (__name__ == "__main__") {
  
  // Hinge example
    translate([-30,30,0])
    rotate([0,0,10]) 
        enhanced_hinge(width=40, length=25, thickness=5 , knuckle_count= 7,stop_angle=90, has_detents = true );
     translate([-30,0,0])
     rotate([0,0,10])
       enhanced_hinge(width=50, length=30, thickness=5   , has_detents=true, detent_angles=[0,45,90,135], tolerance_multiplier=1.1 );
        
     // Ball and Socket Example
    translate([30,30,0])
       ball_socket_joint(ball_diameter= 15,max_angle=45);

       translate([30,0,0])
       ball_socket_joint(ball_diameter = 13,  retention_lip=1, max_angle= 90, tolerance_multiplier = 1.1);
    
  // Living Hinge Example
  translate([-30, -30, 0])
   living_hinge(direction = "horizontal", width= 60, pattern_width= 6, length=40, thickness=3);
 translate([30, -30, 0])
   living_hinge(direction="vertical", width= 30, length=40, thickness=2);
     
  // Snap Fit Example
   translate([0,-70,0])
    snap_fit_joint();

   translate([50,-70, 0])
       snap_fit_joint(snap_type="barb");

     translate([100,-70, 0])
      snap_fit_joint(snap_type="dovetail", mating_clearance=false);

}

// -----
// Documentation
// -----

/*
  General Notes:
  - These joints are designed to be print-in-place when tolerances are tuned correctly.
  - All dimensions are using mm as the unit of measure.
  - Proper calibration of the 3d printer is essential for all tolerances.
    
  Enhanced Hinge Joint Notes:
  - The number of knuckles must be odd in number
  - You can optionally supply detent angles for click positions, this can be usefull for locking parts into specific positions.
  - The stop angle can be used to limit the range of motion if needed
  - There is an optional boolean for detents that enables the detent functionality
  - A tolerance multiplier allows to reduce or increase the existing tolerances
  - Ensure a good first layer to avoid lifting on the print bed.

  Ball and Socket Joint Notes:
  - Can be used for a range of motion joints for custom parts
  - There is a retention lip to prevent parts from seperating easily
  - The ball_diameter parameter adjusts the center of rotation
  - There is a max_angle parameter to help restrict the range of motion
  - A tolerance multiplier allows to reduce or increase the existing tolerances

  Living Hinge Notes:
  - A living hinge bends via a thin section, usually with a repeating cut pattern 
  - Set the direction of flex to either "vertical" or "horizontal" to control flexibility
  - Pattern spacing creates the gaps for flex, smaller spacing increases flexibility
  - Pattern width is equal to the length of the thin flexed area
  - Increasing the pattern depth increases flex, there may be structural concerns
  - A tolerance multiplier allows to reduce or increase the existing tolerances

  Snap Fit Joints Notes: 
  - Has 3 different types of snap features to select
  - Has an option to not add clearances between parts, useful for tight fits.
  - The snap size controls the overall size of the snap
  - The snap_depth controls the engagement of the snap
 - A tolerance multiplier allows to reduce or increase the existing tolerances
  
    
  Troubleshooting Tips
  - Binding Issues: if parts dont move or function
  - Check for excessive tolerances within the utils.scad file
  - Check that a good print speed and resolution are being used
  - Sanding, filing or a razor blade may be needed.
    
 - Snapping Issues
 - If print breaks or is not secure enough try the following:
  - Increase the size of the snap
  - Reduce the size of the mating features to increase engagement
 - If snap joint is too tight
  - Be certain you are using correct calibration for the printer
 - A small amount of sanding or deburring may be needed.
  
  - If parts dont print, consider reducing the print speed, layer height, or increasing extrusion rate.

  Print Orientation Guidelines:
  - Print flat on the bed for maximum strength. There may be a need to add small supports if certain angles are problematic for specific printers
  - Living hinges are easier to print flat without support material

  Assembly Notes:
    - Ensure parts are fully cooled before attempting articulation
    - Make sure to remove any plastic debris before assembly
     -Use a small tool if needed to help make parts move for the first time.
    - Once the part is operational it may be able to move easier with continued use.
*/

```xml
<OPENSCAD>
//-- Common 3D Printing Utilities and Constants --

//-- Constants --
// Layer Height
layer_height = 0.2; // Standard layer height for common printing [mm]

// Nozzle Width
nozzle_width = 0.4; // Standard nozzle width for common printing [mm]

// -- Clearance Values --
// Clearance values for different fit types [mm]
clearance_loose = 0.3; // Loose fit with higher tolerance for movement
clearance_normal = 0.2; // Normal fit
clearance_tight = 0.1; // Tight fit with minimal play
clearance_pressfit = -0.05; // Press fit requires force to assemble

// -- Common Material Properties --
// Although not constants, they illustrate material property placeholders - can be used in future calculations
material_density_pla = 1.24; // [g/cm^3]

// -- Utility Functions --
// Function to create a clearance gap which will increase the size of a geometry
// Parameter 'clearance': desired clearance value to add
// Parameter 'geometry': the geometry to create a clearance gap for.
// Returns a scalable geometry with clearance gap applied
function create_gap(clearance, geometry) =
    resize(
        newsize=geometry.size + 2*clearance,
         geometry);

// Parameter 'dimension': the nominal dimension
// Parameter 'fit_type': fit type string. Can be "loose", "normal", "tight" or "pressfit"
// Returns the tolerance to apply to a dimension, based on desired fit, or zero if an invalid fit string is passed
function calculate_tolerance(dimension, fit_type) =
    let(
        clearance =  fit_type == "loose" ? clearance_loose :
                    fit_type == "normal" ? clearance_normal :
                    fit_type == "tight" ? clearance_tight :
                    fit_type == "pressfit" ? clearance_pressfit : 0
    )
    clearance;


//-- Example Usage/Demonstration --
//Example with a cube without creating the gap, just showing size
$fn=50;
module test_cube(dim){
    cube(dim);
}
module test_clearance_cube(dim, fit){
    diff = calculate_tolerance(dim,fit);
    
    translate([0,dim*2,0])
        cube(dim + diff);
}


test_cube(10);
test_clearance_cube(10, "loose");
test_clearance_cube(10, "normal");
test_clearance_cube(10, "tight");
test_clearance_cube(10, "pressfit");
translate([0,0,20])
    linear_extrude(height = 5)
        text("Testing different tolerances");

translate([0,0,30])
    linear_extrude(height = 5)
        text("loose");
translate([0,20,30])
  linear_extrude(height = 5)
    text("normal");
translate([0,40,30])
    linear_extrude(height = 5)
        text("tight");
translate([0,60,30])
    linear_extrude(height = 5)
        text("pressfit");

     translate ([0,-10,0])
   linear_extrude(height = 5)
    text("Base Cube")
</OPENSCAD>
```


// Mechanical Components Library

// Global Tolerance Variables (adjust based on your printer)
$fn = 50; // global fineness

// Tolerance presets for different fits
tolerance_tight = 0.1;
tolerance_loose = 0.2;
tolerance_press = -0.1;

// Helper function to calculate clearance for given tolerance type
function calculate_clearance(nominal_dimension, tolerance_type) = 
    nominal_dimension + tolerance_type; 


// Function to add radial clearance
function add_radial_clearance(nominal_dimension, clearance) = nominal_dimension + (clearance*2);

// Function to remove radial clearance
function remove_radial_clearance(nominal_dimension, clearance) = nominal_dimension - (clearance*2);



// Module for a printable bearing
// Parameters:
//  - od: Outer diameter
//  - id: Inner diameter
//  - height: Bearing height
//  - num_balls: Number of balls
//  - clearance: Radial clearance between ball and races
// Print Orientation: Vertical (height as Z-axis), without supports
module printable_bearing(od, id, height, num_balls, clearance) {
    
    // Calculate the ball diameter based on the difference between the diameters
    ball_dia = (od - id) / 2 - clearance * 2 ;

    // Ensure that at least 3 balls can be placed
    if (num_balls<3){
        num_balls = 3;
    }
    
    // Sanity check: the ball may not have zero or negative radius.
    if(ball_dia <=0) 
    {
   		echo("Error: Inner diameter too large or outer diameter too small.");
        return;
    }


    // Outer race
    cylinder(h = height, d = od);
    
    // Inner race
    translate([0,0, clearance])
    cylinder(h = height - clearance*2, d = id);
    
    // Ball placement - ensure balls can fit and don't overlap

    for (i = [0:num_balls - 1]) {
        rotate(a=360/num_balls * i)
            translate([(od - ball_dia - clearance * 2)/2, 0, height/2])
                sphere(d = ball_dia);
    }

}

// Module for a simple hinge
// Parameters:
//  - pin_dia: Diameter of the hinge pin
//  - hinge_length: Length of the hinge
//  - hinge_width: Width of the hinge arm
//  - clearance: Clearance between pin and hinge holes
// Print Orientation: flat on the printer bed (hinge length as X-axis or Y-axis); No Supports needed if clearance is sufficient.
module simple_hinge(pin_dia, hinge_length, hinge_width, clearance) {
    
    
    //Left and Right blocks for the hinge
    module hinge_side(len, wid, offset, clear){
     translate([offset, 0,0])
    cube([len, wid, hinge_width]);
    
       translate([len/2,wid/2,0])
        rotate([0,0,90])
        cylinder(h = hinge_width, d=pin_dia+clear);
    }
    
    hinge_side(hinge_length / 2 - 0.1 , hinge_width,0, clearance );
    hinge_side(hinge_length / 2 - 0.1, hinge_width, hinge_length/2 + 0.1, clearance);
   
    
    //Creates the pin
    translate([hinge_length/2, hinge_width/2, 0-tolerance_press])
        cylinder(h=hinge_width*3, d = pin_dia);        
}

// Example usage of both modules
//printable_bearing(od = 20, id = 10, height = 10, num_balls = 6, clearance = 0.2);
//simple_hinge(pin_dia = 5, hinge_length = 30, hinge_width = 15, clearance = 0.2);



//module example_test(){
    // simple_hinge(pin_dia = 5, hinge_length = 30, hinge_width = 15, clearance = 0.1);
   // translate([0,0,20])
    //printable_bearing(od = 20, id = 10, height = 10, num_balls = 6, clearance = 0.1);
//}

//example_test();


```

// Advanced Mechanical Components Library for 3D Printable Fidget Toys
// This library includes advanced mechanisms like Geneva drives, compliant mechanisms,
// advanced bearing types, and compound mechanisms.
// All measurements are in millimeters

include <mechanical_components.scad> // Include basic mechanical components

/* [Global Tolerances - Inherited, but may be overridden per component] */
// Tight tolerance for rotating parts (0.15mm default)
// TIGHT_TOL = 0.15;  // Inherited from mechanical_components.scad
// Standard tolerance for moving parts (0.2mm default)
// STD_TOL = 0.2;  // Inherited from mechanical_components.scad
// Loose tolerance for easy movement (0.3mm default)
// LOOSE_TOL = 0.3;  // Inherited from mechanical_components.scad
// Layer height for calculating vertical tolerances
// LAYER_HEIGHT = 0.2; // Inherited from mechanical_components.scad


/* [Helper Functions - Inherited] */
// Calculate the actual diameter needed for a hole to achieve desired fit
// function get_hole_diameter(nominal_diameter, tolerance) = nominal_diameter + (tolerance * 2);  // Inherited from mechanical_components.scad

// Calculate the actual diameter needed for a shaft to achieve desired fit
// function get_shaft_diameter(nominal_diameter, tolerance) = nominal_diameter - (tolerance * 2); // Inherited from mechanical_components.scad

/* [1. Geneva Drive Mechanism Module] */
// Creates a Geneva drive mechanism for intermittent motion
// Parameters:
//   num_positions: Number of positions of the driven wheel (usually 4, 5, 6, or 8)
//   wheel_radius: Radius of the driven (Geneva) wheel
//   pin_radius: Radius of the driving pin
//   lock_radius: Radius of locking segment
//   height: Height of the mechanism
//   clearance: Clearance for moving parts (default: TIGHT_TOL)
module geneva_drive(num_positions, wheel_radius, pin_radius, lock_radius, height, clearance=TIGHT_TOL) {
    
    // Calculated parameters
    step_angle = 360 / num_positions;
    drive_radius= wheel_radius * sin(step_angle/2);
    
    
    difference(){
        union(){
        
    // Driven wheel (Geneva wheel)
        difference(){
            cylinder(d=wheel_radius*2, h=height, $fn=60);
            
            for(i = [0:num_positions-1]){
              rotate([0,0,i *step_angle + step_angle/2])  
                translate([wheel_radius,0, -0.1])
                    cube([wheel_radius * 2, (wheel_radius/4+ clearance*2) , height+ 0.2],center = true);
             rotate([0,0,i * step_angle])   
                translate([wheel_radius*tan(step_angle/4),0, -0.1])            
                    circle(d=pin_radius*4 + clearance*2, $fn=30 );
              }
             // center hole
            translate([0, 0 , -0.1])
                 cylinder(d=5+clearance*2, h=height+0.2, $fn=30);   
        }
          
        // Driving wheel part, the disk with the pin
        translate([drive_radius, 0,0])
        difference(){
        
                cylinder(d= drive_radius * 2.5, h=height, $fn=60 );
              
            translate([drive_radius,0, -0.1])
                 cylinder(d = (pin_radius * 2 + clearance*2), h=height+0.2, $fn=30 );    
       	  // center hole
            translate([0, 0 , -0.1])
                 cylinder(d=5+clearance*2, h=height+0.2,  $fn=30);
       }
    
    
   //locking segments in 3d 
      for(i = [0: num_positions-1]){
       rotate([0,0,i *step_angle + step_angle/2])     
          translate([drive_radius*cos(step_angle/2+step_angle/4)- lock_radius,  wheel_radius * sin(step_angle/2) ,0])
             
             rotate([0,0,0])
            cylinder(d=lock_radius*2, h=height, $fn=30);
        }
    }
    
  	//clearance cuts for locking components
	translate([drive_radius,0,0])
	 for(i=[0:2]){
           rotate([0,0,i* (360/num_positions) + step_angle/5])
              translate([(wheel_radius)   ,0,-0.1])
                cube([wheel_radius/4   , (wheel_radius/4+ clearance*2)   , height+ 0.2  ], center = true );
       }
    }
    
    
}


/* [2. Compliant Mechanisms Module] */

// Creates a living hinge 
// Parameters:
//   length: length of the hinge
//   width: width of the hinge
//   thickness: thickness of the material
//   hinge_gap: Gap at the center of the hinge
//   num_hinges: number of living hinges
//   clearance: Clearance for part movement
module living_hinge(length, width, thickness, hinge_gap, num_hinges, clearance=TIGHT_TOL) {
   
    
    for (i=[0 : num_hinges-1]) {
      translate([0, i*(width + clearance/2 ) ,0 ])
    difference(){
        cube([length, width, thickness]);
        
          translate([length/2 - hinge_gap/2, (width/2), -0.1])
            cube([hinge_gap, width, thickness + 0.2] , center=true );
    }
   }   
}

// Creates a snap-fit clip
// Parameters:
//   length: length of the clip
//   width: width of the clip
//   height: height of the clip
//   hook_width: width of the hook
//   hook_depth: depth of the hook
//   clearance: Clearance on the hook and slot

module snap_fit_clip(length, width, height, hook_width, hook_depth, clearance = TIGHT_TOL) {
    difference() {
        union() {
            // Base clip
            cube([length, width, height]);

            // Snap-fit hook
            translate([length - hook_depth, 0 , 0])
            cube([hook_depth, width, height]);
             
           
        }
        // hook slot
        translate([length - hook_depth + clearance, width/2, -0.1])
            cube([hook_depth + clearance , (width - hook_width-clearance/2) , height + 0.2] , center = true);
    }
}


// Creates a flexible spring
// Parameters:
//   length: length of the spring
//   width: width of the spring
//   height: height of the spring
//   coil_diameter: diameter of the coil
//   coil_thickness: thickness of the coil
//   num_coils: number of coils
//   clearance: clearance between coils
module flexible_spring(length, width, height, coil_diameter, coil_thickness, num_coils, clearance = TIGHT_TOL) {

    
    for(i=[0: num_coils-1])
    {    
        translate([0 ,(i  *  coil_diameter *1.2+ clearance/2)   , height/2] )
            rotate([0,90,0])
                linear_extrude(height=width){
                    circle(r=coil_diameter/2 - (coil_thickness / 2) ,$fn = 30);
                }    
    }
}


// Creates a bistable mechanism
// Parameters:
//  base_length: Length of the base part
//  base_width: Width of the base part
//  base_height: Height of the base part
//  arm_length: Length of the arm
//  arm_width: Width of the arm
//  arm_thickness: Thickness of the arm
//  pivot_d: Diameter of the pivot
//  clearance: clearance between moving parts

module bistable_mechanism(base_length, base_width, base_height, arm_length, arm_width, arm_thickness, pivot_d, clearance=TIGHT_TOL) {

    //Base
    difference()
    {
        cube([base_length, base_width, base_height]);
        // Pivot cuts
        translate([base_length/2 - arm_length /2, base_width/2, -0.1])
            cylinder(d = pivot_d+clearance*2 , h=base_height + 0.2, $fn=30 );
        
         translate([base_length/2+ arm_length /2, base_width/2, -0.1])
            cylinder(d = pivot_d+clearance*2, h=base_height + 0.2, $fn=30 );  

    }

    //Arms
    translate([0,0,base_height])
    for(i=[-1:1:1])
    
    difference(){
        
        rotate([0,0,i*180])
        
        union()
        {     
            // pivot holder
             translate([base_length/2 - i * arm_length/2,base_width/2 , 0])
                cube([arm_length/4, arm_width, arm_thickness] ,center= [true,false,false] );
            // arm   
            translate([base_length/2 - i * arm_length/2,base_width/2,0])
                cube([ arm_length, arm_width, arm_thickness],center = [true,false,false]);  
                
           
        }   
    	//pivot cut out
        translate([base_length/2 -  i * arm_length/2,base_width/2, -0.1])
            cylinder(d = pivot_d , h = arm_thickness + 0.2, $fn = 30); 
    }    

}


/* [3. Advanced Bearing Types Module] */

// Creates a Herringbone gear bearing
// Parameters:
//   outer_d: Outer diameter of the bearing
//   inner_d: Inner diameter of the bearing
//   height: Height of the bearing
//   num_teeth: Number of gear teeth
//   gear_module: Size of the teeth
//   clearance: Clearance for moving parts (default: TIGHT_TOL)
module herringbone_gear_bearing(outer_d, inner_d, height, num_teeth, gear_module, clearance=TIGHT_TOL) {
    
    pitch_diameter = gear_module*num_teeth;
    
        difference(){
        union(){
        
             cylinder(d = outer_d, h = height, $fn=60);
       
        
            for ( i = [0:num_teeth-1]){
               angle = i * 360 / num_teeth;            
                rotate([0,0,angle])      
                    translate([(pitch_diameter /2 ),0,0])
                       
                            rotate([0,0, i*75/30   ] )                            
                                   linear_extrude(height=height)
                                    polygon( points = [[-gear_module *1.5 , -gear_module ], 
                                                     [-gear_module *1.5, gear_module ],
                                                     [0, gear_module*2.4],
                                                     [gear_module*1.5, gear_module],
                                                      [gear_module*1.5,-gear_module],
                                                     [0,-gear_module*2.4]
                                                     ]);
                rotate([0,0,-90+angle])      
                    translate([(pitch_diameter /2 ),0,0])
                       
                            rotate([0,0, i*75   ] )                            
                                   linear_extrude(height=height)
                                    polygon( points = [[-gear_module *1.5 , -gear_module ], 
                                                     [-gear_module *1.5, gear_module ],
                                                     [0, gear_module*2.4],
                                                     [gear_module*1.5, gear_module],
                                                      [gear_module*1.5,-gear_module],
                                                     [0,-gear_module*2.4]
                                                     ]);
            
             }
            }
             translate([0,0,-0.1])
               cylinder(d = inner_d + clearance*2      , h = height + 0.2, $fn=60);
           }
}



// Creates a crossed roller bearing
// Parameters:
//   outer_d: Outer diameter of the bearing
//     inner_d: Inner diameter of the bearing
//   height: Height of the bearing
//   roller_d: Diameter of the rollers
//   num_rollers: Number of rollers
//   clearance: Clearance for moving parts (default: TIGHT_TOL)
module crossed_roller_bearing(outer_d, inner_d, height, roller_d, num_rollers,clearance=TIGHT_TOL) {
    
     race_width = (outer_d - inner_d) / 4;
    
     
    difference()
    
    {          
        union()
        {
        //outer race
              difference()
              {                  
              
                   cylinder(d=outer_d, h=height   , $fn = 100);
                        
                  translate([0,0,-0.1])
                       cylinder(d=outer_d - race_width*2 - clearance   , h=height + 0.2, $fn = 100);
                        
              
              }
        //inner race
           
          difference()            
          {           
                 cylinder(d=inner_d + race_width*2 , h = height , $fn = 100);
                   translate([0,0,-0.1])
                   cylinder(d=inner_d   , h=height+0.2, $fn = 100);
                 }           
         
         //rollers        
    for(i = [0:num_rollers-1]) {
        angle = i * 360 / num_rollers;
         
              rotate([0, 0, angle+45])
                   translate([
                       (outer_d/2 + inner_d/2)/2 * cos(angle),
                       (outer_d/2 + inner_d/2)/2 * sin(angle),
                       height/2
                   ])              
                cylinder(d=roller_d-clearance*2, h=height, $fn=30);
       
		rotate([0, 0, angle-45])
                   translate([
                       (outer_d/2 + inner_d/2)/2 * cos(angle),
                       (outer_d/2 + inner_d/2)/2 * sin(angle),
                       height/2
                   ])              
                cylinder(d=roller_d-clearance*2, h=height, $fn=30);
            } 
        
        }
          
    }

}


// Creates a self-aligning bearing
// Parameters:
//   outer_d: Outer diameter of the bearing housing
//   inner_d: Inner diameter of the inner sphere
//   ball_d: Diameter of the ball
//   height: Height of the mechanism
//   clearance: Clearance for moving parts (default: TIGHT_TOL)

module self_aligning_bearing(outer_d, inner_d, ball_d, height, clearance=TIGHT_TOL) {

   
    difference(){

        union(){
        
          // Outer housing
        	cylinder(d=outer_d, h=height, $fn=100);
           // Inner sphere
          translate([0, 0, height/2])
            sphere(d=ball_d, $fn=60 );
     
          }
           //Sphere cutout
        translate([0, 0, height/2])
              sphere(d = inner_d + clearance*2, $fn=60);
       translate([0,0,-0.1])
                cylinder(d=inner_d+clearance*2, h=height + 0.2, $fn = 60 );
     }
    
}


// Creates a cage-guided ball bearing
// Parameters:
//   outer_d: Outer diameter of the bearing
//   inner_d: Inner diameter of the bearing
//   height: Height of the mechanism
//   ball_d: Diameter of the balls
//   num_balls: Number of balls
//   clearance: Clearance for moving parts (default: TIGHT_TOL)
module cage_guided_ball_bearing(outer_d, inner_d, height, ball_d, num_balls, clearance=TIGHT_TOL) {
    
    race_width = (outer_d - inner_d) / 4;
    
    difference(){
        
    union(){
       // Outer ring
        difference()
        {
            cylinder(d=outer_d, h=height, $fn=100);
            translate([0,0,-0.1])  
              cylinder(d=outer_d - race_width*2, h=height +0.2 ,$fn=100 );
        }
        // Inner ring
         difference()
        {
            cylinder(d=inner_d + race_width*2, h=height, $fn=100);
            translate([0,0,-0.1])  
              cylinder(d=inner_d, h=height +0.2 ,$fn=100 );
        }
    
         // Ball bearings - cage
        for(i = [0:num_balls-1]) {
            angle = i * 360 / num_balls;        
            translate([
                    (outer_d/2 + inner_d/2)/2 * cos(angle),
                    (outer_d/2 + inner_d/2)/2 * sin(angle),
                    height/2
                 ])
          	difference(){
                    sphere(d=ball_d, $fn=30);
                      	
        			sphere(d=ball_d*0.75 , $fn=30);
            
            		}
           }    
        }

    }
}

/* [4. Compound Mechanisms Module] */

// Creates a differential gear set
// Parameters:
//   carrier_d: Diameter of the carrier
//   sun_d: Diameter of the sun gear
//   planet_d: Diameter of the planet gears
//   height: Height of the mechanism
//   num_planets: Number of planet gears
//   clearance: Clearance for moving parts (default: TIGHT_TOL)

module differential_gear_set(carrier_d, sun_d, planet_d, height, num_planets, clearance=TIGHT_TOL) {

    
    difference(){
      union() {

            // Carrier
                cylinder(d=carrier_d, h=height, $fn=100);
            // Sun gear
           translate([0,0,height/2])
            cylinder(d=sun_d,h=height/2 ,$fn=50);
            // Planet Gears - simplified
            for(i = [0 : num_planets-1]){ 
                angle = i* (360/num_planets) ;
            	translate([carrier_d/2 *cos(angle), carrier_d/2 * sin(angle),0])
                  
                    translate([0,0,height/2]){
                  	        cylinder(d=planet_d, h=height/2 , $fn=30);
                            }
              } 
        }
        //Cutouts for gears
         translate([0,0,-0.1])
       	 cylinder(d= sun_d + clearance*2 , h=height + 0.2 , $fn=50);
            for(i=[0: num_planets-1]) {
                angle = i * 360 / num_planets;
                 translate([carrier_d/2 *cos(angle), carrier_d/2 * sin(angle),-0.1])
                	 cylinder(d= planet_d + clearance*2 ,h =height+0.2, $fn=30 );        
            }      
    }

}


// Creates a harmonic drive mechanism
// Parameters:
//   outer_d: Diameter of the flexspline housing
//   flexspline_d: Diameter of the flexible spline
//   circular_d: Diameter of the circular spline
//   wave_d:Diameter of the wave generator
  //  height: Height of the mechanism
//   clearance: Clearance for moving parts
module harmonic_drive(outer_d, flexspline_d, circular_d, wave_d, height, clearance=TIGHT_TOL) {

    difference(){
        union(){

        // circular spline - very rough approximation here...
             cylinder(d = circular_d, h = height, $fn=100);
        // flexspline - very rough approximation here...
            translate([0,0,height/2])
                cylinder( d = flexspline_d , h = height/2, $fn=100);
       // wave generator
            translate([0,0,height/2])
                cylinder( d = wave_d, h= height/2, $fn=60);

        
        }    
        
         translate([0,0,-0.1])
         	cylinder(d = outer_d + clearance*2 , h= height + 0.2, $fn=100);
         
          translate([0,0,-0.1])
         	cylinder(d = flexspline_d - clearance*2 , h = height/2+0.2, $fn=100);
        
    }    
}

// Creates a simple Schmidt coupling
// Parameters:
    // inner_d: Diameter of the Inner disk
    //outer_d: Diameter of the outer disks
    //height: height of the mechanism
    //clearance: clerance between moving parts
module schmidt_coupling(inner_d, outer_d, height, clearance = TIGHT_TOL){

   union(){
    
    
     //Inner Disk
        cylinder(d=inner_d, h=height/2, $fn= 70);
       
     // outer disks  
       
    for(i = [0:1])
    rotate([0,0, i * 180])
      translate([inner_d/2,0,0]){
            cylinder(d=outer_d, h=height, $fn=70);
      }
    
    
      for(i = [0:1])
      translate([0,0,height/4 + height/4 * i ] )
            cylinder(d=inner_d - clearance*2, h=height/4, $fn=70);       
     }
}

// Creates a universal joint
// Parameters:
//  joint_size: main size of the universal joint
//  height: height of the universal joint
// clearance : clereance between moving parts

module universal_joint(joint_size, height, clearance=TIGHT_TOL) {

    difference(){
        union(){
          //first yoke
        translate([0,0,0])
          cube([joint_size, joint_size / 2 ,height]);
         
            translate([0,joint_size/2 ,0])
                rotate([0, 0,  90])
                  cube([joint_size, joint_size / 2 ,height]);
           
            //middle pin
        translate([joint_size/2,joint_size/2,height/4])
               cylinder(d =joint_size/2,  h = height/2,$fn = 60);
            //second yoke
        translate([0,joint_size ,0])
                 cube([joint_size, joint_size / 2 ,height]);   
      
      }
    
        translate([-0.1,joint_size/4 ,0])
          cube([joint_size+0.2, joint_size/2 + .2, height+0.2], center=false );  
        
         translate([0,joint_size/2 ,-0.1])
        cylinder(d=(joint_size)/4 + 5 + clearance*2,  h = height + 0.2,$fn = 60);
    
        translate([joint_size/2,joint_size/2 ,-0.1])
         cylinder(d = joint_size - 4 + clearance*2, h = height + 0.2,$fn = 60);
      }
}
    


/* [Usage Examples] */
// Example geneva drive
geneva_drive(num_positions=6, wheel_radius=20, pin_radius=3, lock_radius=5, height=8);

// Example living hinge
living_hinge(length = 30, width=5 , thickness=2 , hinge_gap=1.5, num_hinges = 3);

// Example snap-fit clip
snap_fit_clip(length=20, width=5, height=5, hook_width=3, hook_depth=3);

// Example flexible spring
flexible_spring(length=5, width=5 , height=5, coil_diameter=3, coil_thickness=1, num_coils=4);

// Example bistable mechanism
bistable_mechanism(base_length = 50, base_width=10, base_height = 8 , arm_length=20,
                 arm_width=5,arm_thickness=2 , pivot_d=3);
                 
// Example herringbone gear bearing
herringbone_gear_bearing(outer_d=30, inner_d=10, height=8, num_teeth=20, gear_module=1.2);

// Example crossed roller bearing
crossed_roller_bearing(outer_d=40, inner_d=20, height=8, roller_d=4, num_rollers=10);
                 
// Example self-aligning bearing
self_aligning_bearing(outer_d=30, inner_d = 10, ball_d = 20, height = 10 );

// Example cage-guided ball bearing
cage_guided_ball_bearing(outer_d=30, inner_d=15, height=10, ball_d=4, num_balls=8);

// Example differential gear set
differential_gear_set(carrier_d=50, sun_d=15, planet_d=10, height=8, num_planets=3);

// Example harmonic drive
harmonic_drive(outer_d=40, flexspline_d=25, circular_d=30, wave_d=15, height=10);

// Example schmidt coupling
schmidt_coupling(inner_d = 15, outer_d=20,height = 8);

// Example universal joint
universal_joint(joint_size=30, height=10);

// Advanced Fidget Toy Showcase
// Demonstrates multiple complex print-in-place mechanisms
include <../lib/mechanical_components.scad>
include <../lib/fidget_components.scad>
include <../lib/advanced_mechanics.scad>

/* [Global Parameters] */
// Overall size of the fidget toy (diameter of the base)
BASE_DIAMETER = 80;
// Height of the base plate
BASE_HEIGHT = 6;
// Thickness for walls and mechanism mounting points
WALL_THICKNESS = 3;
// Main clearance setting
CLEARANCE = TIGHT_TOL;

/* [Main Assembly] */
module advanced_fidget_showcase() {
  difference() {
    union() {
      // 1. Base Structure - Hexagonal base with rounded corners and main body
      base_structure();
      
      // 2. Geneva Drive Mechanism - Center
      translate([0, 0, BASE_HEIGHT])
          geneva_drive_center();
      
      // 3. Herringbone Gear Bearing - Outer Ring
      translate([0, 0, BASE_HEIGHT+10])
        herringbone_gear_bearing_outer();
  
      // 4. Bistable Clicking Mechanisms - On edges
      bistable_clicks_edges();
  
       // 5. Living Hinges - Flexible elements
       living_hinges_elements();
        
       // 6. Self-Aligning Bearing Assembly
         translate([0, 0, BASE_HEIGHT+25])
        self_aligning_bearing_assembly();
       
    }
       // Cutouts for visual interest and weight reduction
       pattern_cutouts();
  }
}
    
    
/* [Helper Modules] */

// Creates the hexagonal base plate with rounded corners and mounting points
module base_structure() {
    linear_extrude(height = BASE_HEIGHT)
        offset(r=5)
        polygon(points=[
            [BASE_DIAMETER/2, 0],
            [BASE_DIAMETER/4, BASE_DIAMETER * sin(PI/3)/2],
            [-BASE_DIAMETER/4, BASE_DIAMETER * sin(PI/3)/2],
            [-BASE_DIAMETER/2, 0],
            [-BASE_DIAMETER/4, -BASE_DIAMETER * sin(PI/3)/2],
            [BASE_DIAMETER/4, -BASE_DIAMETER * sin(PI/3)/2],
         ]);
    // Mounting points for mechanisms
    translate([0,0,BASE_HEIGHT]){
       
            cylinder(d=BASE_DIAMETER/3, h = WALL_THICKNESS , $fn=60);
         
        	for (i=[0:5]){
                 rotate([0,0,i*60])
                 translate([BASE_DIAMETER*0.4,0,0])
                     cylinder(d=8,h = WALL_THICKNESS, $fn=30);
            }
    }
}


// Creates the Geneva Drive assembly at the center
module geneva_drive_center(){
    geneva_drive(num_positions=4, wheel_radius=20, pin_radius=3, lock_radius=5, height=10, clearance=CLEARANCE);
}

// Creates the outer herringbone gear bearing for rotation around the center
module herringbone_gear_bearing_outer(){    
  herringbone_gear_bearing(outer_d=60, inner_d=50, height=10, num_teeth=20, gear_module=1.2, clearance = CLEARANCE);       
}


// Creates bistable clicking mechanisms at each edge of the hexagon
module bistable_clicks_edges() {
    for (i=[0:5]){
        rotate([0,0,i*60]){
         translate([BASE_DIAMETER*0.4,0,(2)])
            bistable_mechanism(base_length = 15, base_width=10, base_height = 6 , arm_length=8,
                 arm_width=4,arm_thickness=2 , pivot_d=2, clearance = CLEARANCE);
        }
    }
}

module living_hinges_elements(){
     for(i=[0:2])
       {
        rotate([0,0,i*120+60])  
        translate([BASE_DIAMETER /2.5,-2, BASE_HEIGHT/2 + 0.1])  
            living_hinge(length = 15, width=5 , thickness=2 , hinge_gap=1.5, num_hinges = 2, clearance=CLEARANCE);
        }
      for(i=[0:2])
       {
        rotate([0,0,i*120+60])  
        translate([-BASE_DIAMETER /2.5,2, BASE_HEIGHT/2 + 0.1])
          rotate([0,0,180])
             living_hinge(length = 15, width=5 , thickness=2 , hinge_gap=1.5, num_hinges = 2, clearance=CLEARANCE);
        }
}


// Creates the Self Alingning bearing above other mechanisms
module self_aligning_bearing_assembly() {
    self_aligning_bearing(outer_d=30, inner_d=15, ball_d=25, height=14, clearance=CLEARANCE);
}


// Creates decorative cutouts for weight reduction across each hex face
module pattern_cutouts() {
    cutout_size = 4;
    
     for (i = [0:5]){
        rotate([0,0,i*60])
        for(x = [1:2:7]){
             translate([x*BASE_DIAMETER/10   ,BASE_DIAMETER/3, BASE_HEIGHT/2])
                cylinder(d=cutout_size, h= BASE_HEIGHT + 0.2, $fn=20);
        }
        for(x = [-1:2:-7]){
             translate([x*BASE_DIAMETER/10 ,BASE_DIAMETER/3, -0.1])
                cylinder(d=cutout_size, h= BASE_HEIGHT + 0.2, $fn=20);
        }
    }
    
    for (i = [0:5]){
        rotate([0,0,i*60])
        translate([0,BASE_DIAMETER/3, BASE_HEIGHT/2])
          cylinder(d = 5, h = BASE_HEIGHT + 0.2 , $fn=30);
    }
}


/* [Main] */
// Render the complete advanced fidget toy
advanced_fidget_showcase();

/* [Printing Instructions]
This is a complex print-in-place model with multiple mechanisms.
Recommended print settings:
- Layer height: 0.15mm - 0.2mm (0.15 if possible for finer details)
- Infill: 20%
- Perimeters: 3
- Top/Bottom layers: 4
- Print speed: 30-40mm/s (consider reducing speed for accuracy)
- Print temperature: As appropriate for your filament
- Build plate adhesion: Brim recommended (due to size and complexity)
- No supports needed
- Print orientation: Flat with the hexagonal base on the print surface
Important Notes:
- Start with test prints for tolerances if needed
- Clean up any stringing or artifacts carefully
- Ensure your printer is well-calibrated
- Test each mechanisms in place after print is finsished.
*/



#!/usr/bin/env python3
"""
OpenSCAD Generator for Fidget Toys
Generates OpenSCAD code for fidget mechanisms using physical calculations.
"""

import os
import argparse
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

@dataclass
class Material:
    """Represents material properties"""
    name: str
    density: float # g/cm³
    friction: float
    youngs_modulus: float # Pa
    yield_strength: float # Pa


@dataclass
class DesignConfig:
    """Represents overall design configurations"""
    tolerance : float = 0.15
    layer_height : float = 0.2
    material: Material = Material(
            name="PLA",
            density=1.24, 
            friction=0.35,
            youngs_modulus=3.5e9,
            yield_strength = 50e6
    )

# Define base classes for mechanisms
class FidgetMechanism:
    """Base class for fidget mechanisms"""
    def __init__(self, name: str, config: DesignConfig):
        self.name = name
        self.config = config
    
    def generate_scad(self) -> str:
        """Generate OpenSCAD code (to be implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement generate_scad method")
    
    def _header(self) -> str:
        """Generates the header block and includes"""
        return f"""// {self.name} - Generated by OpenSCAD Generator
include <mechanical_components.scad>
include <advanced_utilities.scad>
include <fidget_utilities.scad>
include <physics_utilities.scad>
include <testing_utilities.scad>


TIGHT_TOL = {self.config.tolerance};
STD_TOL = {self.config.tolerance + 0.05};
LOOSE_TOL = {self.config.tolerance + 0.15};
LAYER_HEIGHT = {self.config.layer_height};

"""
    
    def _footer(self) -> str:
        """Generates the footer"""
        return f"//{self.name} generated successfully"
    
    def _render(self, scad_code: str) -> str:
        """Combines header, scad code, and footer"""
        return f"""{self._header()}

{scad_code}

{self._footer()}"""


class ClickMechanism(FidgetMechanism):
    """Class for click mechanisms"""
    def __init__(self, name: str, config: DesignConfig, diameter: int = 25,
                 height: int = 5, clicks: int = 12, click_depth: float = 0.8,
                 button_size: int = 15, button_travel: float = 1.5):
        super().__init__(name, config)
        self.diameter = diameter
        self.height = height
        self.clicks = clicks
        self.click_depth = click_depth
        self.button_size = button_size
        self.button_travel = button_travel

    
    def generate_scad(self) -> str:
        scad_code = f"""
module {self.name}_click_mechanism() {{
    click_wheel(
        diameter={self.diameter},
        height={self.height},
        clicks={self.clicks},
        click_depth={self.click_depth},
        clearance = TIGHT_TOL
    );
    translate([0,30,0])
    tactile_button(
        size={self.button_size},
        height={self.height + self.button_travel},
        travel={self.button_travel},
        clearance = TIGHT_TOL
    );
}}

{self.name}_click_mechanism();
"""
        return self._render(scad_code)

class SpinMechanism(FidgetMechanism):
    """Class for spin mechanisms"""
    def __init__(self, name: str, config: DesignConfig, diameter: int = 40,
                 height: int = 8, weight_holes: int = 3, hole_size: int = 8,
                 momentum_inner_d: int = 40, momentum_outer_d: int = 50,
                 weight_count: int = 6):
        super().__init__(name, config)
        self.diameter = diameter
        self.height = height
        self.weight_holes = weight_holes
        self.hole_size = hole_size
        self.momentum_inner_d = momentum_inner_d
        self.momentum_outer_d = momentum_outer_d
        self.weight_count = weight_count
    
    def generate_scad(self) -> str:
        scad_code = f"""
module {self.name}_spin_mechanism() {{
    weighted_spinner(
        diameter={self.diameter},
        height={self.height},
        weight_holes={self.weight_holes},
        hole_size={self.hole_size},
        clearance = TIGHT_TOL
    );
    translate([0, 30, 0])
        momentum_ring(
            outer_d={self.momentum_outer_d},
            inner_d={self.momentum_inner_d},
            height={self.height},
            weight_count={self.weight_count},
            clearance = TIGHT_TOL
        );
}}

{self.name}_spin_mechanism();
"""
        return self._render(scad_code)

class HingeMechanism(FidgetMechanism):
    """Class for hinge mechanisms"""
    def __init__(self, name: str, config: DesignConfig, width: int = 20,
                 height: int = 10, thickness: int = 3, angle: int = 45,
                 length: int = 20, hinge_width: float = 0.8, spacing: int = 2,
                 flex_segments: int = 5):
        super().__init__(name, config)
        self.width = width
        self.height = height
        self.thickness = thickness
        self.angle = angle
        self.length = length
        self.hinge_width = hinge_width
        self.spacing = spacing
        self.flex_segments = flex_segments

    def generate_scad(self) -> str:
        scad_code = f"""
module {self.name}_hinge_mechanism() {{
    bistable_hinge(
       width={self.width},
       height={self.height},
       thickness={self.thickness},
       angle={self.angle},
       clearance =  TIGHT_TOL
    );
     translate([0, 25, 0])
        living_hinge_pattern(
           length={self.length},
           width={self.width/2},
           hinge_width={self.hinge_width},
           spacing={self.spacing}
        );
     translate([0,-25,0])
        flex_joint(
            length={self.length},
            width={self.width/2},
            thickness={self.thickness/2},
            segments={self.flex_segments}
        );
}}

{self.name}_hinge_mechanism();
"""
        return self._render(scad_code)
    

class SlideMechanism(FidgetMechanism):
    """Class for slide mechanisms"""
    def __init__(self, name: str, config: DesignConfig, width: int = 30, 
                 height: int = 30 ,pattern_size : int = 2, depth : float= 0.3, 
                 grip_width : int = 20, grip_height : int = 20, grip_pattern : str ="diamond"):
        super().__init__(name, config)
        self.width = width
        self.height = height
        self.pattern_size = pattern_size
        self.depth = depth
        self.grip_width = grip_width
        self.grip_height = grip_height
        self.grip_pattern = grip_pattern
        
    def generate_scad(self) -> str:
        scad_code = f"""
module {self.name}_slide_mechanism() {{
     silent_slide_surface(
        width = {self.width},
        height = {self.height},
        pattern_size = {self.pattern_size},
        depth = {self.depth}
        );
      translate([0, 40 ,0])
        grip_pattern(
            width = {self.grip_width},
            height =  {self.grip_height},
            pattern = "{self.grip_pattern}"
        );   
    }}

{self.name}_slide_mechanism();
"""
        return self._render(scad_code)

    
class TestPieceGenerator(FidgetMechanism):
    """Class for generating the testing utilities"""
    def __init__(self, name: str, config: DesignConfig, features: Optional[list]=None):
        super().__init__(name, config)
        self.features = features if features else ["clearance","strength", "bridging"]
    
    def generate_scad(self) -> str:
         scad_code = f"""
module {self.name}_test_piece() {{
    test_piece(features = {self.features});
}}

{self.name}_test_piece();
"""
         return self._render(scad_code)
       
# Implementation of physical calculations (using math library)
class PhysicsUtils:
    """Class for physical calculations"""
    
    @staticmethod
    def get_disk_inertia(mass: float, radius: float) -> float:
      """Calculates inertia of disk"""
      return mass * radius**2/2
    
    @staticmethod
    def get_spin_time(inertia: float, initial_velocity: float, friction_coef: float, radius: float, g : float = 9.81) -> float:
           """Calculate spin time based on the provided values (using meters and kg)"""
           return inertia * initial_velocity / (friction_coef * g * radius)

    @staticmethod
    def get_optimal_weight_dist(total_mass: float, outer_radius : float) -> Tuple [float, float]:
      """Calculates optimal weight distribution between rim and core"""
      core_mass = total_mass * 0.3
      rim_mass = total_mass * 0.7
      return core_mass, rim_mass

    @staticmethod
    def get_part_mass(volume: float, material: Material ) -> float:
        """Calculate mass based on material and volume"""
        return volume * material.density
    
    @staticmethod
    def get_click_force(thickness: float, length: float, deflection: float, material: Material) -> float:
        """Calculate spring force for a click mechanism"""
        youngs_modulus= material.youngs_modulus
        moment_inertia = thickness**4 / 12
        return 3 * youngs_modulus * moment_inertia * deflection / length**3
    
    @staticmethod
    def get_min_thickness(length: float, force: float, material: Material) -> float:
          """Calculate minimum thickness for durability"""
          yield_strength = material.yield_strength
          return  math.sqrt(6 * force * length/ yield_strength)
      
    @staticmethod
    def get_bearing_friction(load: float, radius: float, friction_coef: float) -> float:
        """Calculate friction in bearing"""
        return load * radius * friction_coef
    
def main():
    """Main command-line interface"""
    parser = argparse.ArgumentParser(description="OpenSCAD Fidget Toy Generator")
    parser.add_argument("-t", "--type", required=True,
                        choices=["click", "spin", "hinge", "slide","test"],
                        help="Type of fidget mechanism to generate")
    parser.add_argument("-o", "--output", default="output.scad",
                        help="Output file name (default: output.scad)")
    parser.add_argument("--tolerance", type=float, default=0.15,
                        help="Tolerance (default: 0.15)")
    parser.add_argument("--layer_height", type=float, default=0.2,
                        help="Layer height (default: 0.2)")
    parser.add_argument("--material", default="PLA", choices=["PLA", "ABS", "PETG", "NYLON"] ,
                        help = "Material to be used (default PLA)")

    args = parser.parse_args()
    
    # Configure Material
    if args.material =="PLA":
         material = Material(
            name="PLA",
            density=1.24, 
            friction=0.35,
            youngs_modulus=3.5e9,
            yield_strength = 50e6
        )

    elif args.material =="ABS":
         material = Material(
             name="ABS",
            density=1.04, 
            friction = 0.40,
           youngs_modulus = 2.3e9,
            yield_strength= 40e6
        )        
            
    elif args.material =="PETG":
        material = Material(
              name="PETG",
            density=1.27, 
           friction=0.30,
           youngs_modulus=2.9e9,
           yield_strength=45e6
        )
        
    elif args.material =="NYLON":
         material = Material(
             name="NYLON",
             density = 1.13,
            friction=0.25,
           youngs_modulus=2.8e9,
           yield_strength=60e6
        )   
    else:
            material = Material(
            name="PLA",
            density=1.24, 
            friction=0.35,
            youngs_modulus=3.5e9,
            yield_strength= 50e6    
        )        
             
    config = DesignConfig(tolerance=args.tolerance, layer_height = args.layer_height, material = material)
    
    if args.type == "click":
        mechanism = ClickMechanism(name="parametric_click", config=config)
    elif args.type =="spin":
          mechanism = SpinMechanism(name="parametric_spin", config=config)
    elif args.type =="hinge":
          mechanism = HingeMechanism(name="parametric_hinge", config=config)
    elif args.type =="slide":
         mechanism = SlideMechanism(name = "parametric_slide", config=config)   
    elif args.type =="test":
         mechanism = TestPieceGenerator(name = "test_piece", config = config)
    else:
        print("Invalid mechanism type, valid values are 'click', 'spin', 'hinge', 'slide'")
        exit()


    try:
        scad_code = mechanism.generate_scad()
      
        dir_path = os.path.dirname(args.output)
        if dir_path and not os.path.exists(dir_path):
             os.makedirs(dir_path)

        with open(args.output, "w") as f:
           f.write(scad_code)
        
        print(f"OpenSCAD code generated successfully: {args.output}")
    
    except Exception as e:
        print(f"Error generating OpenSCAD code: {e}")

if __name__ == "__main__":
    main ()

#!/usr/bin/env python3
"""
Python script to generate OpenSCAD code for fidget toys.
Includes classes for different mechanisms and SCAD code generation tools.
"""

import os
import math
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

# Constants for physical calculations
GRAVITY = 9.81  # m/s²
PI = math.pi
ABS_FRICTION = 0.40 
PLA_FRICTION = 0.35
PETG_FRICTION = 0.30

# Base directory for the generated SCAD files
SCAD_OUTPUT_DIR = "generated_scad"
TEMPLATE_DIR = "templates"

class Material(Enum):
    """ Enum for common 3D printing materials """
    PLA = auto()
    PETG = auto()
    ABS = auto()
    NYLON = auto()

MATERIAL_PROPERTIES = {
    Material.PLA: {"density": 1.24, "friction": PLA_FRICTION, "youngs_modulus": 3.5e9, "yield_strength": 50e6},
    Material.PETG: {"density": 1.27, "friction": PETG_FRICTION, "youngs_modulus": 2.9e9, "yield_strength": 45e6},
    Material.ABS: {"density": 1.04, "friction": ABS_FRICTION, "youngs_modulus": 2.3e9, "yield_strength": 40e6 },
    Material.NYLON:  {"density": 1.13, "friction": 0.25, "youngs_modulus":  2.8e9, "yield_strength":  60e6}
}


@dataclass
class BaseMechanism:
    """Base class for all mechanisms, handles common properties"""
    name: str
    size: float
    height: float
    material: Material = Material.PLA
    clearance: float = 0.2
    
    def get_material_prop(self, prop: str):
        return MATERIAL_PROPERTIES[self.material][prop]
    
    def generate_parameters_scad(self) -> str:
        """Generates SCAD code for the mechanism's parameters"""
        return f"""
// Parameters for {self.name}
SIZE = {self.size};
HEIGHT = {self.height};
CLEARANCE = {self.clearance};
MATERIAL = "{self.material.name}";
"""

@dataclass
class ClickMechanism(BaseMechanism):
  
    clicks: int = 12
    click_depth: float = 0.8
    
    def generate_scad_code(self) -> str:
        """Generates SCAD code for a click mechanism using existing utilities"""
  
        return f"""
module {self.name}_module() {{
    click_wheel(diameter=SIZE, height=HEIGHT, clicks={self.clicks}, click_depth={self.click_depth}, clearance=CLEARANCE);

    translate([0, SIZE*1.7, 0])
         tactile_button(size=SIZE/2, height=HEIGHT, travel=SIZE/10, snap_force = ABS({self.get_material_prop("youngs_modulus")/5e9}) );
    
    translate([0, -SIZE*1.7, 0])
      smooth_detent(diameter=SIZE/2, height=HEIGHT, force = ABS({self.get_material_prop("friction")}/5) );
  }}       
{self.name}_module();
        """
    
@dataclass
class SpinMechanism(BaseMechanism):
    """Class representing a spinning mechanism with physics calculations and SCAD code."""
    mass : float
    weight_holes: int = 3
    hole_size: float = 8.0
    
    def calculate_moment_of_inertia(self, mass: float) -> float:
        """Calculate moment of inertia for a disk."""
        radius = self.size / 2
        return mass * (radius ** 2) / 2
    
    def calculate_spin_time(self, inertia: float, initial_velocity: float) -> float:
           """Calculates spin time based on initial velocity and friction."""
           radius = self.size / 2
           material_friction = self.get_material_prop("friction")        
           return (inertia * initial_velocity) / (material_friction * GRAVITY * radius)    
    
    def calculate_optimal_weight_distribution(self, total_mass: float) -> Tuple[float, float]:
        """Calculate optimal weight distribution for maximum spin time."""
        core_mass = total_mass * 0.3
        rim_mass = total_mass * 0.7
        return core_mass, rim_mass

    
    def generate_scad_code(self) -> str:
            """Generates SCAD code for a spinning fidget toy using existing modules"""


            return f"""
module {self.name}_module() {{
  weighted_spinner(diameter=SIZE, height=HEIGHT, weight_holes={self.weight_holes}, hole_size={self.hole_size}, clearance=CLEARANCE);
  
    translate([0,SIZE*1.7,0])
          momentum_ring(outer_d= SIZE + SIZE/2 , inner_d=SIZE, height=HEIGHT);
    translate([0,-SIZE*1.7,0])
          dampened_bearing_race(outer_d=SIZE, inner_d=SIZE/2 ,height=HEIGHT );
}}
{self.name}_module();
"""

@dataclass
class HingeMechanism(BaseMechanism):
    """Class representing a hinge mechanism."""
    hinge_width: float = 5
    hinge_spacing: float = 2

    def generate_scad_code(self) -> str:
            """Generates SCAD code for a hinge mechanism using existing modules"""
            return f"""
module {self.name}_module() {{
    bistable_hinge(width=SIZE, height=HEIGHT, thickness={self.size/4} , clearance = CLEARANCE);
     translate([0, SIZE*1.7, 0])
       living_hinge_pattern(length=SIZE*1, width={self.hinge_width} , hinge_width={self.hinge_width/5} ,spacing = {self.hinge_spacing} );
     translate([0, -SIZE*1.7, 0])
      flex_joint(length = SIZE,  width = HEIGHT , thickness = {self.size/4} , segments = 5);  
}}
{self.name}_module();
"""

@dataclass
class CombinedMechanism(BaseMechanism):
    """A Mechanism combining multiple existing mechanisms"""
    mechanism_list: List[str]
    
    def generate_scad_code(self) -> str:
        """Generates SCAD code for the fidget toy including multiple mechanisms"""
        
        mechanism_calls = "".join(f"""
        translate([0, {i*self.size*2}, 0])
        {mech}_module();
        """ for i, mech in enumerate(self.mechanism_list) )

        return f"""
module {self.name}_module() {{
  {mechanism_calls}
}}
{self.name}_module();
"""

@dataclass
class TestGenerator:
    """Generates SCAD code including example modules and templates"""
    output_dir: str = SCAD_OUTPUT_DIR
    include_paths: List[str] = field(default_factory=list)
    mechanism: Optional[BaseMechanism] = None

    def ensure_directory(self):
        """Ensures the output directory exists"""
        os.makedirs(self.output_dir, exist_ok=True)

    def add_include_path(self, path: str):
        """Adds paths to be included in the output
        
        Args: path: Path to the SCAD library
            
        """
        self.include_paths.append(path)
        
    def load_template(self, filename) -> str:
         """Safely loads SCAD template from given path"""
         file_path =  os.path.join(TEMPLATE_DIR, filename) 
         
         try:
             with open(file_path, "r") as f:
                 return f.read()
         except FileNotFoundError:
             raise FileNotFoundError(f"Template file not found: {file_path}")
    
    def generate_include_statements(self) -> str:
        """Generates SCAD include statements"""
        return "\n".join(f"include <{path}>;" for path in self.include_paths)

    def add_customizer_parameters(self) -> str:
                """Generates SCAD code to easily customize parameters in customizer"""
                if self.mechanism:
                    return self.mechanism.generate_parameters_scad()
                return ""
    
    def generate_scad_file(self, filename="fidget_toy.scad"):
        """Generates the SCAD file"""
        self.ensure_directory()
        file_path = os.path.join(self.output_dir, filename)
        
        try:            
            template = self.load_template("base_template.scad")
          
            scad_code = f"""
{self.generate_include_statements()}
{self.add_customizer_parameters()}
{self.mechanism.generate_scad_code() if self.mechanism else ""}
"""
            
            scad_code = template.replace('///<CUSTOM_CODE>', scad_code)
            
            with open(file_path, 'w') as f:
                f.write(scad_code)

            print(f"SCAD file generated successfully: {file_path}")
            
        except Exception as e:
          
            print(f"Error generating SCAD file")
            raise
        
        return file_path

def main() -> None:
  """Main fuction to test the classes and generate a few test examples"""
  
  #setup example paths
  example_includes = [
    "../lib/mechanical_components.scad",
    "../lib/advanced_utilities.scad",
    "../lib/fidget_utilities.scad",
     "../lib/physics_utilities.scad"
]
    
  #Example 1, a basic clicker
  clicker = ClickMechanism(name="basic_clicker", size=20, height=6, clicks=10)
  test_generator = TestGenerator(include_paths=example_includes, mechanism=clicker)
  test_generator.generate_scad_file(filename="basic_clicker.scad")
  
  # Example 2, A basic spinner example
  spinner = SpinMechanism(name="basic_spinner", size =25, height = 8, mass= 25 )
  test_generator2 = TestGenerator(include_paths=example_includes, mechanism=spinner)
  test_generator2.generate_scad_file(filename="basic_spinner.scad")
  
   #Example 3, a basic hinge example
  hinger = HingeMechanism(name="basic_hinge", size=15, height = 5 )
  test_generator3 = TestGenerator(include_paths=example_includes, mechanism=hinger)
  test_generator3.generate_scad_file(filename="basic_hinge.scad")
  
  #Example 4 combined mechanisms.
  fidget_toy = CombinedMechanism(name="combined_fidget", size=15, height=8, mechanism_list=["basic_clicker","basic_spinner","basic_hinge"]  )
  combined_gen = TestGenerator(include_paths=example_includes, mechanism = fidget_toy)
  combined_gen.generate_scad_file(filename="combined_toy.scad")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Creates a showcase model demonstrating different fidget toy mechanisms
with detailed error handling and path setup
"""

import os
import sys
import traceback

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

try:
    print("Current directory:", os.getcwd())
    print("Python path:", sys.path)
    print("\nAttempting to import modules...")
    
    from fidget_generator.mechanisms import (
        SpinMechanism, ClickMechanism, HingeMechanism, CombinedMechanism, Material
    )
    print("Successfully imported mechanisms")
    
    from fidget_generator.generator import ScadGenerator, TestGenerator, create_mechanism_showcase
    print("Successfully imported generator")
    
    import create_showcase
    print("\nRunning create_showcase.main()...")
    create_showcase.main()
    
except ImportError as e:
    print(f"\nImport Error: {str(e)}")
    print("\nTraceback:")
    traceback.print_exc()
    
except Exception as e:
    print(f"\nError type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print("\nTraceback:")
    traceback.print_exc()
    sys.exit(1)

import os
import sys
import traceback

try:
    # Add the current directory to Python path
    sys.path.insert(0, os.getcwd())
    

    # Construct the full path to the templates directory using the current file's directory
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
    # Create templates directory if it doesn't exist
    os.makedirs(templates_dir, exist_ok=True)
    
    # Construct the full path to the template file
    template_file = os.path.join(templates_dir, "base_template.scad")

    # Create a basic template file if it doesn't exist
    if not os.path.exists(template_file):
        with open(template_file, "w") as f:
            f.write("""// Base template for generated SCAD files
/* [Global Parameters] */

///<CUSTOM_CODE>
""")
    

    print("Running create_showcase.main()...")
    
    # Dynamically import create_showcase after ensuring the path is correct
    import create_showcase
    create_showcase.main()
    
except ImportError as e:
    print(f"\nImport Error: {str(e)}")
    print("\nPython path:", sys.path)
    print("\nTraceback:")
    traceback.print_exc()
    sys.exit(1)
    
except Exception as e:
    print(f"\nError type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print("\nTraceback:")
    traceback.print_exc()
    sys.exit(1)

import subprocess
import os
import sys

def run_powershell_command():
    script = """
    cd 'C:\\mygit\\BLazy\\repo\\scad\\models'
    .\\venv\\Scripts\\Activate.ps1
    $env:PYTHONPATH = '.'
    python create_showcase.py
    """
    
    try:
        # Write script to a temporary file
        with open('run_showcase.ps1', 'w') as f:
            f.write(script)
            
        # Run PowerShell script
        result = subprocess.run([
            'powershell.exe',
            '-ExecutionPolicy', 'Bypass',
            '-File', 'run_showcase.ps1'
        ], capture_output=True, text=True)
        
        # Print output and errors
        print("Output:", result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
            
        return result.returncode
        
    except Exception as e:
        print(f"Error running PowerShell script: {e}")
        return 1
    finally:
        # Cleanup
        if os.path.exists('run_showcase.ps1'):
            os.remove('run_showcase.ps1')

if __name__ == "__main__":
    sys.exit(run_powershell_command())

import os
import sys
import subprocess

try:
    print("Current directory:", os.getcwd())
    print("Checking virtual environment...")
    venv_path = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
    if os.path.exists(venv_path):
        print(f"Found virtual environment python at: {venv_path}")
    else:
        print("Warning: Virtual environment python not found")

    print("\nChecking create_showcase.py...")
    showcase_path = os.path.join(os.getcwd(), "create_showcase.py")
    if os.path.exists(showcase_path):
        print(f"Found create_showcase.py at: {showcase_path}")
        with open(showcase_path, 'r') as f:
            print("First few lines of create_showcase.py:")
            print(''.join(f.readlines()[:5]))
    else:
        print("Warning: create_showcase.py not found")

    print("\nChecking run_showcase.py...")
    run_script_path = os.path.join(os.getcwd(), "run_showcase.py")
    if os.path.exists(run_script_path):
        print(f"Found run_showcase.py at: {run_script_path}")
        print("\nAttempting to run with debug output...")
        
        result = subprocess.run(
            [sys.executable, run_script_path],
            capture_output=True,
            text=True
        )
        
        print("\nCommand Output:")
        print(result.stdout)
        
        if result.stderr:
            print("\nErrors:")
            print(result.stderr)
            
        print(f"\nReturn code: {result.returncode}")
    else:
        print("Warning: run_showcase.py not found")
        
except Exception as e:
    print(f"\nError: {type(e).__name__}")
    print(f"Message: {str(e)}")
    sys.exit(1)

import os
import sys
import subprocess

def ensure_directory():
    target_dir = r"C:\mygit\BLazy\repo\scad\models"
    if os.getcwd() != target_dir:
        os.chdir(target_dir)
        print(f"Changed directory to: {os.getcwd()}")

try:
    print("Current directory:", os.getcwd())
    ensure_directory()
    
    # Create templates directory if needed
    os.makedirs("templates", exist_ok=True)
    
    # Create base template if needed
    template_path = os.path.join("templates", "base_template.scad")
    if not os.path.exists(template_path):
        with open(template_path, "w") as f:
            f.write("""// Base template for generated SCAD files
/* [Global Parameters] */

///<CUSTOM_CODE>
""")
    
    print("\nExecuting create_showcase.py...")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    
    # Use virtual environment python if available
    python_exe = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
    if not os.path.exists(python_exe):
        python_exe = sys.executable
        print(f"Using system python: {python_exe}")
    else:
        print(f"Using venv python: {python_exe}")
    
    result = subprocess.run(
        [python_exe, "create_showcase.py"],
        env=env,
        capture_output=True,
        text=True
    )
    
    print("\nCommand Output:")
    print(result.stdout)
    
    if result.stderr:
        print("\nErrors:")
        print(result.stderr)
    
    print(f"\nReturn code: {result.returncode}")
    
except Exception as e:
    print(f"\nError: {type(e).__name__}")
    print(f"Message: {str(e)}")
    sys.exit(1)

# Run test script with full output capture
Write-Host "Current directory: $PWD"
Write-Host "Running test script..."
Write-Host ""

$env:PYTHONPATH = "C:\mygit\BLazy\repo\scad\models"
$venvPython = ".\venv\Scripts\python.exe"
$testScript = ".\test_imports.py"

if (Test-Path $venvPython) {
    Write-Host "Using virtual environment Python at: $venvPython"
    $result = & $venvPython $testScript 2>&1
    
    Write-Host "Output:"
    $result | ForEach-Object { Write-Host $_ }
} else {
    Write-Host "Virtual environment Python not found at: $venvPython"
    Write-Host "Trying system Python..."
    
    $result = & python $testScript 2>&1
    Write-Host "Output:"
    $result | ForEach-Object { Write-Host $_ }
}

Write-Host "`nScript completed with exit code: $LASTEXITCODE"

<!DOCTYPE html>
 <html lang="en">
 <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fidget Toy Catalog</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" integrity="sha512-9usAa10IRO0HhonpyAIVpjrylPvoDwiPUiKdWk5t3PyolY1cOd4DSE0Ga+ri4AuTroPR5aQvXU9xC6qOPnzFeg==" crossorigin="anonymous" referrerpolicy="no-referrer" />
    <style>
        .card-img-top {
            max-height: 200px; /* Adjust as needed */
            object-fit: contain;
            padding: 10px;
        }

        .card {
             margin-bottom: 20px;
         }
    </style>
 </head>
 <body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <a class="navbar-brand" href="/">Fidget Factory</a>
    <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
    <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarNav">
    <ul class="navbar-nav">
    <li class="nav-item active">
    <a class="nav-link" href="/">Home <span class="sr-only">(current)</span></a>
    </li>
    <li class="nav-item">

    </li>

    </ul>
    </div>
    </nav>
    <div class="container mt-4">
        <h1>Welcome to the Fidget Factory!</h1>
        <p>Explore our collection of print-in-place fidget toys. These toys are designed to be printed as a single piece, with moving parts that are ready to go right off the print bed! </p>
        
         <h2>Available Fidget Toys</h2>
        <div class="row" id = "fidget-grid">
              
                <div class="col-sm-6 col-md-4 col-lg-3">
                <div class="card">
                 <i class="fa-solid fa-gear" style ="font-size:100px; text-align:center; padding:20px;"></i>
                    <div class="card-body">
                        <h5 class="card-title">Gear Fidget</h5>
                        <p class="card-text">A simple fidget toy with rotating gears.</p>
                         <a href="/customize?model=gear_fidget" class="btn btn-primary">Customize</a>
                         </div>
                </div>
            </div>


             <div class="col-sm-6 col-md-4 col-lg-3">
                 <div class="card">
                   <i class="fa-solid fa-spinner" style ="font-size:100px; text-align:center; padding:20px;"></i>

                    <div class="card-body">
                        <h5 class="card-title">Spinner Fidget</h5>
                        <p class="card-text">A simple fidget toy with a spinning center.</p>
                         <a href="/customize?model=spinner_fidget" class="btn btn-primary" >Customize</a>
                    </div>
            </div>
           </div>
      
          <div class="col-sm-6 col-md-4 col-lg-3">
                <div class="card">
                     <i class="fa-solid fa-chain" style ="font-size:100px; text-align:center; padding:20px;"></i>
                    <div class="card-body">
                        <h5 class="card-title">Chain Fidget</h5>
                        <p class="card-text">A fidget toy with flexible links.</p>
                         <a href="/customize?model=chain_fidget" class="btn btn-primary">Customize</a>
                    </div>
            </div>
         </div>
  
  
        <div class="col-sm-6 col-md-4 col-lg-3">
                <div class="card">
                    <i class="fa-solid fa-circle-nodes" style ="font-size:100px; text-align:center; padding:20px;"></i>
                    <div class="card-body">
                        <h5 class="card-title">Ball Joint Fidget</h5>
                         <p class="card-text">A fidget toy with articulating ball joints.</p>
                           <a href="/customize?model=ball_joint_fidget" class="btn btn-primary">Customize</a>
                    </div>
                </div>
            </div>

        </div>
        
        
       <h2>How to Customize</h2>
       <p>To customize a fidget toy, simply click the "Customize" button below the toy's description. This will take you to the customization page, where you can modify the parameters of your chosen toy to your liking. After customizing, you can generate a downloadable model file for 3D printing.</p>


    </div>
    
     <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.3/dist/umd/popper.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
 </body>

from flask import Flask, render_template, request
import os
import json

app = Flask(__name__)

# Dummy data for demonstration - Replace with actual logic
available_models = {
    'gears': {
        'name': 'Gears',
        'parameters': [
            {'name': 'num_teeth', 'label': 'Number of Teeth', 'type': 'number', 'min': 5, 'max': 50, 'default': 20},
            {'name': 'gear_diameter', 'label': 'Gear Diameter (mm)', 'type': 'number', 'min': 10, 'max': 100, 'default': 50},
            {'name': 'thickness', 'label': 'Thickness (mm)', 'type': 'number', 'min': 2, 'max': 10, 'default': 5}

        ],
        'print_recommendations': "Use a strong and durable filament like PLA or PETG. Layer height around 0.2mm for good detail."
        },
    'bearing': {
        'name': 'Bearing',
        'parameters': [
             {'name': 'outer_diameter', 'label': 'Outer Diameter (mm)', 'type': 'number', 'min': 15, 'max': 80, 'default': 40},
              {'name': 'inner_diameter', 'label': 'Inner Diameter (mm)', 'type': 'number', 'min': 5, 'max': 30, 'default': 15},
                {'name': 'bearing_thickness', 'label': 'Thickness (mm)', 'type': 'number', 'min': 3, 'max': 15, 'default': 8}

        ],
            'print_recommendations': "PETG recommended for durability and smooth movement. 0.2mm layer height and appropriate supports."
        },
    'spinner': {
        'name': 'Spinner',
        'parameters': [
             {'name': 'outer_diameter', 'label': 'Outer Diameter (mm)', 'type': 'number', 'min': 50, 'max': 100, 'default': 70},
              {'name': 'center_diameter', 'label': 'Center Diameter (mm)', 'type': 'number', 'min': 10, 'max': 30, 'default': 19},
                {'name': 'thickness', 'label': 'Thickness (mm)', 'type': 'number', 'min': 5, 'max': 15, 'default': 8}

        ],
            'print_recommendations': "PLA or ABS work well. Use a 0.2mm or lower layer height for good surface finish. Supports may be required for complex designs."
        }
}

@app.route('/', methods=['GET', 'POST'])
def customize():
    selected_model = request.args.get('model', 'gears')  # Default to 'gears'
    model_data = available_models.get(selected_model)


    if request.method == 'POST':

        form_data = {}
        for param_data in model_data['parameters']:
           param_name = param_data['name']
           form_data[param_name]= request.form.get(param_name, param_data['default'])

        print(form_data)
        # Here you would ideally call the code to generate the STL with parameters
        # and serve the preview. For simplicity will return some dummy data back.
        # Handle STL generation and preview here
        # Preview rendering with Three.js and STL loading will be handled on client side.

        stl_file = "dummy.stl" #dummy name not used here
        # Pass data to the template, including selected model parameters and the STL filename
        return render_template('customize.html', models=available_models, selected_model=selected_model, model_data = model_data, submitted=True, form_data=form_data,  stl_file = stl_file)

    return render_template('customize.html', models=available_models, selected_model=selected_model, model_data = model_data, submitted=False)


@app.route('/advanced_options')
def advanced_options():
    # Route for handling advanced options form separately if needed
    return "Advanced Options Coming soon"


if __name__ == '__main__':
    app.run(debug=True)

import subprocess
import os
import sys
import json
import logging
from pythonfiles import fidget_generator  # Import existing module

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
SCAD_DIR = "scadfiles"
STL_DIR = "stls"
PYTHON_DIR = "pythonfiles"

# Ensure directories exist
os.makedirs(STL_DIR, exist_ok=True)
os.makedirs(PYTHON_DIR, exist_ok=True)

def run_openscad_command(command):
    """
    Executes an OpenSCAD command using subprocess.

    Args:
        command (list): List of strings representing the command.

    Returns:
        tuple: (return code, stdout, stderr)
    """
    try:
        logging.info(f"Executing command: {' '.join(command)}")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        stdout_str = stdout.decode('utf-8').strip()
        stderr_str = stderr.decode('utf-8').strip()
        return_code = process.returncode

        if return_code != 0:
          logging.error(f"OpenSCAD command failed with code {return_code}. Stderr:\n{stderr_str}")
        else:
          logging.info(f"OpenSCAD command successful, Stdout: \n{stdout_str}")
        return return_code, stdout_str, stderr_str

    except FileNotFoundError:
        logging.error("OpenSCAD executable not found. Is it installed and in your PATH?")
        return -1, "", "OpenSCAD executable not found"
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return -1, "", str(e)

def generate_stl_from_scad(scad_file, output_stl_file, parameters=None):
    """
    Generates an STL file from an OpenSCAD file.

    Args:
        scad_file (str): Path to the SCAD file.
        output_stl_file (str): Path to save the generated STL file.
        parameters (dict, optional): Dictionary of parameters to pass to OpenSCAD. Defaults to None.
    Returns:
        bool: True if successful, False otherwise.
    """
    if not os.path.exists(scad_file):
       logging.error(f"SCAD file not found: {scad_file}")
       return False

    command = ["openscad", "-o", output_stl_file]
    
    if parameters:
      for key, value in parameters.items():
        command.append(f"-D{key}={value}")

    command.append(scad_file)


    return_code, _, stderr = run_openscad_command(command)
    if return_code == 0:
        logging.info(f"Successfully generated STL file: {output_stl_file}")
        return True
    else:
        logging.error(f"Failed to generate STL file: {output_stl_file}. Error:\n{stderr}")

        return False
    


def parse_scad_parameters(scad_file):
    """
    Reads an SCAD file and extracts its parameters.

    Args:
        scad_file (str): Path to the SCAD file.

    Returns:
        dict: Dictionary of parameters (key-value) or None if parsing fails.
    """
    try:
        with open(scad_file, 'r') as f:
            content = f.read()
            
            #This is a very basic method of getting the parameters right now. 
            #A more robust method (AST parsing) would be more ideal
            #Example parameter declarations 'parameter = 10;' and 'parameter = "text";'
            
            lines = content.split(';')
            parameter_declarations = [line.strip() for line in lines if any(keyword in line for keyword in ["=", "parameter"])]
            
            
            parameters = {}
            for declaration in parameter_declarations:
                parts = declaration.split("=", 1)
                if len(parts) == 2:
                    name = parts[0].split('parameter ')[1].strip() if 'parameter ' in parts[0] else parts[0].strip()
                    value = parts[1].strip()
                    
                    #Attempt to parse to int, string, float
                    try:
                        value = int(value)
                    except ValueError:
                         try:
                            value = float(value)
                         except ValueError:
                            if '"' in value:
                                value  = value.replace('"', '') #remove quotes from string parameters
                    parameters[name] = value
            return parameters
    except FileNotFoundError:
        logging.error(f"SCAD file not found: {scad_file}")
        return None
    except Exception as e:
        logging.error(f"Error parsing parameters: {e}")
        return None


def validate_parameters(parameters, expected_types):
    """
    Validates parameters against expected types.

    Args:
        parameters (dict): Dictionary of parameters to validate.
        expected_types (dict): Dictionary of parameter names and expected types.

    Returns:
        dict: Validated parameters or None if validation fails.
    """
    if not parameters:
      logging.error("No parameters given to validate")
      return None
    if not expected_types:
       logging.error("No expected_types given to validate with")
       return None

    validated_params = {}
    for key, expected_type in expected_types.items():
        if key not in parameters:
            logging.error(f"Missing parameter: {key}")
            return None;
        value = parameters[key]
        if not isinstance(value, expected_type) :
            logging.error(f'Invalid type for parameter "{key}": expected {expected_type}, got {type(value)}')
            return None

        validated_params[key] = value
    return validated_params
def create_preview_image(scad_file, output_png_file, parameters=None):
    """
        Generates a preview image from a scad file.
        Args:
            scad_file (str): Path to the SCAD file.
            output_png_file (str): Path to save the generated image.
            parameters (dict, optional): Dictionary of parameters to pass to OpenSCAD. Defaults to None.

        Returns:
            bool: True if successful, False otherwise.
        """
    if not os.path.exists(scad_file):
       logging.error(f"SCAD file not found: {scad_file}")
       return False

    command = ["openscad", "-o", output_png_file, "-d", "2D"]
    
    if parameters:
      for key, value in parameters.items():
        command.append(f"-D{key}={value}")

    command.append(scad_file)

    return_code, _, stderr =  run_openscad_command(command)

    if return_code == 0:
        logging.info(f"Successfully generated preview image: {output_png_file}")
        return True
    else:
        logging.error(f"Failed to generate preview image: {output_png_file}. Error:\n{stderr}")
        return False
def get_fidget_types():
     """
        Gets a list of available fidget types from the SCAD files.
        Returns:
            list: list of available fidget type filenames (without extension) or None if directory is missing/empty
      """
     if not os.path.exists(SCAD_DIR):
          logging.error(f"SCAD directory ({SCAD_DIR}) not found")
          return None

     scad_files = [f for f in os.listdir(SCAD_DIR) if f.lower().endswith(".scad")]
     if not scad_files:
          logging.error(f"No SCAD files found in {SCAD_DIR}")
          return None
     return [os.path.splitext(f)[0] for f in scad_files]
def handle_file_operation(operation_type, file_path, content=None):
     """
        Handles file operations such as read write or delete
     """
     try:
          if operation_type == "read":
              if not os.path.exists(file_path):
                  logging.error(f"File does not exist: {file_path}")
                  return None;
              with open(file_path, 'r') as file:
                return file.read()
          elif operation_type == "write":
          
              with open(file_path, 'w') as file:
                  if content!= None:
                     file.write(content)
                  else:
                        logging.error("No content to write")
                        return None
              return True
          elif operation_type == "delete":
              if os.path.exists(file_path):
                  os.remove(file_path)
                  return True;
              else:
                logging.error(f"File does not exist to delete: {file_path}")
                return False
          else:
                logging.error(f"Unsuported operation: {operation_type}")
                return None;          
     except Exception as e:
                logging.error(f"Error performing file operation: {e} ")
                return None
def main():
     # Example usage:
     
     # Example usage
    fidget_types = get_fidget_types()
    if fidget_types:
        logging.info(f"Available fidget types: {fidget_types}")
    else:
         logging.error("No fidget types available")
         return
    
    #Lets get the name of a scad file we know exists from the list
    scad_file_name = f"{fidget_types[0]}.scad"     
    scad_file = os.path.join(SCAD_DIR, scad_file_name)
    stl_file = os.path.join(STL_DIR, f"{os.path.splitext(scad_file_name)[0]}.stl")
    png_file = os.path.join(STL_DIR, f"{os.path.splitext(scad_file_name)[0]}.png")
   
    
    
    
    # 1. Parse parameters first
    parameters = parse_scad_parameters(scad_file)
    if parameters:
        logging.info(f"Parameters from {scad_file}: {parameters}")
    else:
         logging.error(f"Could not get parameters from {scad_file}, exiting")
         return
         
    #2. Now let's validate them.
    #Hard coding the types for now, since for simplicity's sake they will all be numbers
    expected_types = {key: (int if isinstance(val, int) else (float if isinstance(val, float) else str)) for key, val in parameters.items()}

    validated_parameters = validate_parameters(parameters, expected_types)
    if validated_parameters:
         logging.info(f"Validated Parameters: {validated_parameters}")
    else:
         logging.error(f"Parameter validation failed for {scad_file}, exiting")
         return


    # 3. Generate STL file
    stl_generated = generate_stl_from_scad(scad_file, stl_file, validated_parameters)
    if stl_generated:
        logging.info(f"STL file generated successfully: {stl_file}")
    else:
         logging.error(f"Could not generate STL file {stl_file}")

    #4 Generate Preview Image
    image_preview_success = create_preview_image(scad_file, png_file, validated_parameters)
    if image_preview_success:
           logging.info(f"preview image generated successfully {png_file}")
    else:
         logging.error(f"Could not generated preview image {png_file}")

    
    # Example handling file read operation
    file_content = handle_file_operation("read", scad_file)
    if file_content:
        logging.info(f"File content of {scad_file}:\n{file_content[:100]}...(truncated)")
    else:
        logging.error("Failed to read file")
    temp_file = os.path.join(PYTHON_DIR, "temp.txt");
    # Example handling file write operation
    file_write_success = handle_file_operation("write",temp_file, "Test content")
    if file_write_success:
         logging.info(f"Successfully wrote data to: {temp_file}")
         # Example handling file delete operation
         file_delete_success = handle_file_operation("delete",temp_file)
         if file_delete_success:
              logging.info(f"Successfully deleted file: {temp_file}")

         else:
              logging.error(f"Error deleting file: {temp_file}")

    else:
         logging.error(f"Failed to write data to: {temp_file}")
   

if __name__ == "__main__":
    main()

import * as THREE from 'three';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';


let scene, camera, renderer, controls, stlObject;
let previousParameters = {};
let previewMode = 'default'; // Can be 'default', 'wireframe', etc.

function init(containerId) {
    const container = document.getElementById(containerId);
    if(!container){
        console.error("Container not found: ", containerId);
      return;
    }
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x444444); // Set scene background color

    // Camera setup
    camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.z = 50;


    // Renderer setup
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);


    // Light
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.8); 
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight( 0xffffff, 0.3);
    directionalLight.position.set(5, 5, 5)
    scene.add( directionalLight);


    // Controls
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true; // Enable damping for smoother camera movement
    controls.dampingFactor = 0.05;
    controls.enableZoom = true;
    controls.zoomSpeed = 1.2;
    controls.minDistance = 5; // Minimum zoom distance
    controls.maxDistance = 150; // Maximum zoom distance
    controls.addEventListener('change', render); // Re-render on control change

    window.addEventListener('resize', onWindowResize);

    animate();
}


function loadSTLModel(stlfile){
     const loader = new STLLoader();
    
      loader.load( stlfile, function ( geometry ) {
    
        const material = new THREE.MeshPhongMaterial( { color: 0xffffff, specular: 0x111111, shininess: 100, side: THREE.DoubleSide } );
        
        
        if (stlObject) {
            scene.remove(stlObject);
            stlObject.geometry.dispose();
           
          }
        stlObject = new THREE.Mesh(geometry,material);

        // Center the model
        geometry.computeBoundingBox();
        const center = geometry.boundingBox.getCenter(new THREE.Vector3());
        stlObject.position.sub(center)

         // Scale to a standard size
            const maxSize = Math.max(geometry.boundingBox.max.x - geometry.boundingBox.min.x,
                        geometry.boundingBox.max.y - geometry.boundingBox.min.y,
                        geometry.boundingBox.max.z - geometry.boundingBox.min.z);
               
             if (maxSize > 0) {
                const scaleFactor = 30/ maxSize;
                stlObject.scale.set(scaleFactor,scaleFactor, scaleFactor);
                stlObject.geometry.computeBoundingBox(); // Recompute bounds after scaling
            }
        
        scene.add(stlObject);
        if(previewMode === 'wireframe'){
            updateMaterialWireframe();
          } else {
             updateMaterialDefault();
        }
        render();
    
      });
}



function updateMaterialWireframe(){
        if(stlObject){
             stlObject.material.wireframe = true;
             
        }


}
function updateMaterialDefault(){
    if(stlObject){
        stlObject.material.wireframe = false;
    }
}
function updateModel(parameters, stlfile) {

    if (JSON.stringify(previousParameters) !== JSON.stringify(parameters)) {
      loadSTLModel(stlfile)
      previousParameters = { ...parameters }; // Deep copy
    }
 
}


function setPreviewMode(mode) {
    previewMode = mode;
    
    if (stlObject) {
         if (mode === 'wireframe') {
          updateMaterialWireframe();
        }
        else{
            updateMaterialDefault();
        }
        render();
      }
}

function onWindowResize() {
    const container = renderer.domElement.parentElement;

    if(!container){
        console.error("Container not found for resize");
      return;
    }
        
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();

    renderer.setSize(container.clientWidth, container.clientHeight);
    render();
}
function animate() {
    requestAnimationFrame(animate);
    controls.update();
    render();
}
function render(){
    renderer.render(scene,camera);
}
export{ init, loadSTLModel, updateModel, setPreviewMode, render}

/* styles.css */

/* General Styles */
body {
    font-family: sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f8f9fa; /* light grey background */
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

/* Navigation Bar Styles */
.navbar {
    background-color: #343a40; /* dark background */
    padding: 10px 0;
    margin-bottom: 20px;
}

.navbar-brand {
    color: white !important;
    font-weight: bold;
    font-size: 1.5rem;
}
.navbar-brand:hover{
  color: white !important;
}

.navbar-nav .nav-link {
    color: rgba(255, 255, 255, 0.7) !important;
    margin-left: 15px;
}

.navbar-nav .nav-link:hover {
    color: rgba(255, 255, 255, 1) !important;
}

/* Card Styles for Model Display */
.card {
    border: 1px solid #dee2e6; /* light border */
    margin-bottom: 20px;
    box-shadow: 0 0 10px rgba(0,0,0,0.1); /* shadow for depth */
    transition: 0.3s;
}

.card:hover {
    box-shadow: 0 0 15px rgba(0,0,0,0.2);
    transform: translateY(-5px);
}

.card-body {
    padding: 20px;
}

.card-img-top {
    max-height: 200px;
    object-fit: cover;
}


/* Form Styles for Customization Page */
.form-group {
    margin-bottom: 20px;
}

label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

input[type="text"],
input[type="number"],
select,
textarea {
    width: 100%;
    padding: 10px;
    border: 1px solid #ced4da; /* light border */
    border-radius: 4px;
    box-sizing: border-box;
}

textarea{
  height: 150px;
}


/* Preview Container Styling */
#preview-container {
    border: 1px dashed #ced4da; /* grey border */
    padding: 20px;
    margin-bottom: 20px;
    text-align: center;
}

#preview-container img {
  max-width: 100%;
  max-height: 400px;
  object-fit: contain;
  margin: auto;
  
}



/* Responsive Design Adjustments - Example breakpoints */
@media (max-width: 768px) {
    .container {
        padding: 10px;
    }
    .card{
      margin-bottom: 10px;
    }
    .navbar-brand{
      font-size:1.25rem;
    }
    .navbar-nav{
      margin-top: 10px;
    }
    .navbar-nav .nav-link{
        margin-left: 0px;
    }
    
}



/* Custom Button Styles  */
.btn-custom {
    background-color: #007bff; /* blue */
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    transition: 0.3s;
    display: inline-block;

}

.btn-custom:hover {
    background-color: #0056b3; /* darker blue on hover */
}


.btn-custom-secondary {
    background-color: #6c757d; /* grey */
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    transition: 0.3s;
    display: inline-block;
}
.btn-custom-secondary:hover {
    background-color: #5a6268; /* darker grey on hover */
}

/* Loading Indicators */
.loading-indicator {
    text-align: center;
    margin: 20px;
    font-size: 1.2rem;
}

.spinner {
    border: 4px solid rgba(0, 0, 0, 0.1);
    border-top: 4px solid #3498db;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    animation: spin 1s linear infinite;
    display: inline-block;
    margin-bottom: 10px;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}



/* Error Message Styling */
.error-message {
    color: #dc3545; /* red for error */
    text-align: center;
    margin: 20px;
    font-weight: bold;
}

/* Style for hidden elements*/
.hidden{
  display:none;
}
