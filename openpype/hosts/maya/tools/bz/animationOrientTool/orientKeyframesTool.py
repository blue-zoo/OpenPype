#
#
#
# Tool to re orient keyframes so master controller is in contant position

import maya.cmds as mc

# Return if node is an anim controller
def is_char_control(node):
    returner = False
    if mc.nodeType(node) in ['transform','joint']:
        if mc.attributeQuery('animControl',node=node,exists=1):
            returner = True
    return returner


class Reorient_Controllers():

    def __init__(self):
        self.active_controllers = []
        self.contoller_reorient = False
        self.position_matrix = False
        self.positional_time_dict = {}

    def ui(self):
        if mc.window("re_orient_keyframes", exists=True):
            mc.deleteUI("re_orient_keyframes")
        self.window = mc.window("re_orient_keyframes",t='Re Orient KeyFrames',s=0)
        self.row_col = mc.rowColumnLayout(nc=2)
        self.first_col = mc.columnLayout(p=self.row_col,adj=1)
        self.second_col = mc.columnLayout(p=self.row_col,adj=1)

        self.controllers_list = mc.textScrollList(p=self.first_col)
        self.add_button = mc.button(p=self.second_col,label = 'Add Controller',c=self.add_controller)
        self.remove_button = mc.button(p=self.second_col,label = 'Remove Controller',c=self.remove_controller)
        mc.separator(p=self.second_col,st='doubleDash')
        self.add_button = mc.button(p=self.second_col,label = 'Re Order Up',c=self.up_controller)
        self.remove_button = mc.button(p=self.second_col,label = 'Re Order Down',c=self.down_controller)
        mc.separator(p=self.second_col,st='doubleDash')

        self.bake_controllers = mc.button(p=self.second_col,label = 'RE BAKE',h=120,c=self.bake)
        self.rorient_controllers = mc.textFieldButtonGrp(p=self.first_col,bl='Controller to Re-Orient',ed=False,bc=self.add_re_orient_controller)
        self.rebake_method_radio = mc.radioButtonGrp( p=self.first_col,numberOfRadioButtons=2, label='Baking Method:  ',select=2, labelArray2=['Set by Matrices', 'Set by Constraints'] )
        mc.showWindow()

    def add_controller(self,test_arg=False,*args):
        if test_arg:
            mc.textScrollList(self.controllers_list,e=1,append=test_arg)
            self.active_controllers.append(test_arg)
        else:
            sel = mc.ls(sl=1)
            items = mc.textScrollList(self.controllers_list,q=1,ai=1)
            if items == None:
                items = []
            for node in sel:
                if is_char_control(node):
                    if not node in items:
                        mc.textScrollList(self.controllers_list,e=1,append=node)
                        self.active_controllers.append(node)

    def remove_controller(self,*args):
        items = mc.textScrollList(self.controllers_list,q=1,ai=1)
        sel_item = mc.textScrollList(self.controllers_list,q=1,si=1)
        if items == None:
            items = []
        if sel_item:
            items = mc.textScrollList(self.controllers_list,e=1,ri=sel_item)
            if sel_item in self.active_controllers:
                self.active_controllers.remove(sel_item)

    def up_controller(self,*args):
        sel_item = mc.textScrollList(self.controllers_list,q=1,si=1)
        if sel_item:

            sel_item_index = mc.textScrollList(self.controllers_list,q=1,sii=1)
            if not sel_item_index == [1]:
                mc.textScrollList(self.controllers_list,e=1,ap=[sel_item_index[0]-1,sel_item[0]])
                other_item = mc.textScrollList(self.controllers_list,q=1,sii=sel_item_index[0]-1)
                mc.textScrollList(self.controllers_list,e=1,rii=other_item)

    def down_controller(self,*args):
        sel_item = mc.textScrollList(self.controllers_list,q=1,si=1)
        if sel_item:
            #print sel_item
            sel_item_index = mc.textScrollList(self.controllers_list,q=1,sii=1)
            #print sel_item_index
            mc.textScrollList(self.controllers_list,e=1,ap=[sel_item_index[0]+2,sel_item[0]])
            other_item = mc.textScrollList(self.controllers_list,q=1,sii=sel_item_index[0]+2)
            mc.textScrollList(self.controllers_list,e=1,rii=other_item)

    def add_re_orient_controller(self,test_arg=False,*args):
        if test_arg:
            mc.textFieldButtonGrp(self.rorient_controllers,e=1,tx=test_arg)
            self.contoller_reorient = test_arg
            self.position_matrix = test_arg

        else:
            sel = mc.ls(sl=1)
            mc.textFieldButtonGrp(self.rorient_controllers,e=1,tx=sel[0])
            self.contoller_reorient = sel[0]
            self.position_matrix = sel[0]



    def add_position_x_controller(self,test_arg=False,*args):
        if test_arg:
            mc.textFieldButtonGrp(self.controller_tobake,e=1,tx=test_arg)
            self.position_matrix = test_arg

        else:
            sel = mc.ls(sl=1)
            mc.textFieldButtonGrp(self.controller_tobake,e=1,tx=sel[0])
            self.position_matrix = sel[0]

    def sanity_check(self):
        # Sanity
        cont = 0
        pass_check = True
        for controller in self.active_controllers:
            if not mc.objExists(controller):
                cont +=1
        if cont > 0:
            run()
            mc.warning('Tool Could not Find Controllers to act on, Restarting')
            return False

        else:
            if not mc.objExists(self.contoller_reorient):
                run()
                mc.warning('Tool Could not Find Master Control to bake keys to, Restarting')

            if not mc.objExists(self.position_matrix):
                run()
                mc.warning('Tool Could not find locator Master Control to bake keys to, Restarting')
                pass_check = False
        if pass_check:
            return True
        else:
            return False

    def bake(self,*args):
        if self.sanity_check():
            #print "sel",mc.radioButtonGrp(self.rebake_method_radio,q=1,select = 1)
            if mc.radioButtonGrp(self.rebake_method_radio,q=1,select = 1) ==1:
                self.generate_positional_matrix()
            else:
                self.generate_positional_constraint()

# Bake out sampling Matrices (can be dodgey with controllers pivots)
    def generate_positional_constraint(self):
        try:

            self.locators = []
            self.start_time = mc.playbackOptions(q=1,min=1)
            self.end_time = mc.playbackOptions(q=1,max=1)

            times = self.return_times()


            # Build the dict of positions
            current_time = mc.currentTime(q=1)
            positional_locator = {
                                'tx':mc.getAttr(self.position_matrix+".tx"),
                                'ty':mc.getAttr(self.position_matrix+".ty"),
                                'tz':mc.getAttr(self.position_matrix+".tz"),
                                'rx':mc.getAttr(self.position_matrix+".rx"),
                                'ry':mc.getAttr(self.position_matrix+".ry"),
                                'rz':mc.getAttr(self.position_matrix+".rz")
                                       }

            # Build Dictionary
            for control in self.active_controllers:
                self.positional_time_dict[control]={}
                for time in times:
                    self.positional_time_dict[control][time] = {}

            # Sample Times
            for time in times:
                mc.currentTime(time)
                for control in self.active_controllers:

                    locator = mc.spaceLocator(name = "ctl"+control+"_"+str(time))
                    self.locators.append(locator)
                    constr = mc.parentConstraint(control,locator,mo=False)

                    # Get Attrs
                    mc.delete(constr)
                    self.positional_time_dict[control][time] = {
                                                                'locator':locator
                                                                }




            # For all frames through time
            for time in times:
                # Set Time
                #print "\nCurrent Time: ",time
                mc.currentTime(time)
                # Set root control to start
                mc.setAttr(self.position_matrix+".tx",positional_locator['tx'])
                mc.setAttr(self.position_matrix+".ty",positional_locator['ty'])
                mc.setAttr(self.position_matrix+".tz",positional_locator['tz'])
                mc.setAttr(self.position_matrix+".rx",positional_locator['rx'])
                mc.setAttr(self.position_matrix+".ry",positional_locator['ry'])
                mc.setAttr(self.position_matrix+".rz",positional_locator['rz'])
                #print "Keying to Default Position: ",self.position_matrix
                # Key into position
                key_control_attrs(self.contoller_reorient)


                for control in self.active_controllers:
                    #print "Working on Control ",control

                    # Get Keyframe node and unplug
                    attr_keynodes = {}
                    for attr in ['tx','ty','tz','rx','ry','rz']:
                        attr_keynodes[attr] = False
                        connections = mc.listConnections(control+"."+attr,s=1,d=0,p=1) or []
                        if not connections == []:
                            attr_keynodes[attr] = connections[0]
                            #print "Disconnecting ",connections[0]," from ", control+"."+attr
                            mc.disconnectAttr(connections[0],control+"."+attr)



                    # constrain the control to the locator and get Values
                    locator = self.positional_time_dict[control][time]['locator']
                    constr = mc.parentConstraint(locator,control,mo=False)
                    tx = mc.getAttr(control+".tx")
                    ty = mc.getAttr(control+".ty")
                    tz = mc.getAttr(control+".tz")
                    rx = mc.getAttr(control+".rx")
                    ry = mc.getAttr(control+".ry")
                    rz = mc.getAttr(control+".rz")

                    # Delete Constraint
                    mc.delete(constr)

                    #print attr_keynodes
                    # Reconnect the anim Curve
                    for attr in ['tx','ty','tz','rx','ry','rz']:
                        connected = attr_keynodes[attr]
                        if connected:
                            mc.connectAttr(connected,control+"."+attr)

                    # Set back the sampled curve values
                    mc.setAttr(control+".tx",tx)
                    mc.setAttr(control+".ty",ty)
                    mc.setAttr(control+".tz",tz)
                    mc.setAttr(control+".rx",rx)
                    mc.setAttr(control+".ry",ry)
                    mc.setAttr(control+".rz",rz)


                    key_control_attrs(control)
        except Exception as e:
            print("Failed as :",e.args)
            for node in self.locators:
                try:
                    if mc.objExists(node[0]):
                        mc.delete(node[0])
                except:
                    pass
        finally:

            mc.refresh(su=0)
            mc.currentTime(current_time)
    # Bake out sampling Matrices (can be dodgey with controllers pivots)

    def generate_positional_matrix(self):
        try:
            mc.refresh(su=1)
            self.start_time = mc.playbackOptions(q=1,min=1)
            self.end_time = mc.playbackOptions(q=1,max=1)

            times = self.return_times()


            # Build the dict of positions
            current_time = mc.currentTime(q=1)
            positional_locator = mc.xform(self.position_matrix,q=1,ws=1,m=1)
            for control in self.active_controllers:
                self.positional_time_dict[control]={}
                for time in times:
                    self.positional_time_dict[control][time] = {}


            for time in times:
                mc.currentTime(time)
                for control in self.active_controllers:
                    local_matrix = mc.xform(control,q=1,matrix=1,os=1)
                    world_space = mc.xform(control,q=1,matrix=1,ws=1)
                    self.positional_time_dict[control][time] = {'ws_matrix':world_space,'local_matrix':local_matrix}


            # Apply the ws positions at to controllers once localised
            for time in times:
                mc.currentTime(time)
                mc.xform(self.contoller_reorient,ws=1,m=positional_locator)
                key_control_attrs(self.contoller_reorient)

                for control in self.active_controllers:
                    matrix = self.positional_time_dict[control][time]['ws_matrix']
                    mc.xform(control,ws=1,m=matrix)
                    key_control_attrs(control)
        except Exception as e:
            print("Failed as :",e.args)
        finally:
            mc.refresh(su=0)
            mc.currentTime(current_time)

    def return_times(self):
        keytimes = []
        for controller in self.active_controllers:
            keyframes = mc.keyframe(controller, time=( self.start_time , self.end_time), query=True)
            if not keyframes in [[],None]:
                keytimes.extend(keyframes)

        keyframes = mc.keyframe(self.contoller_reorient, time=( self.start_time , self.end_time), query=True)
        if not keyframes in [[],None]:
            keytimes.extend(keyframes)
        keytimes = remove_duplicates(keytimes)
        keytimes.sort()

        return keytimes


def remove_duplicates(seq):
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if x not in seen and not seen_add(x)]

def key_control_attrs(node):
    mc.setKeyframe(node, attribute='translateX')
    mc.setKeyframe(node, attribute='translateY')
    mc.setKeyframe(node, attribute='translateZ')
    mc.setKeyframe(node, attribute='rotateX')
    mc.setKeyframe(node, attribute='rotateY')
    mc.setKeyframe(node, attribute='rotateZ')

def run():
    inst = Reorient_Controllers()
    inst.ui()
