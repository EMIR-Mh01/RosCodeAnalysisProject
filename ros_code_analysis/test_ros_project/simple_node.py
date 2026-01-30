import rospy
from std_msgs.msg import String

rospy.init_node("simple_node")

pub = rospy.Publisher("/chatter", String, queue_size=10)
sub = rospy.Subscriber("/chatter", String, lambda msg: msg)

rospy.spin()

