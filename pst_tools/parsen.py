# -*- coding: utf-8 -*-
"""


@author: egc
"""
from pst import Pest
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plots

class ParSen(Pest):
    def __init__(self, basename, jco_df = None, drop_regul = False, 
                 drop_groups = None, keep_groups = None, keep_obs = None, 
                 remove_obs = None):
        Pest.__init__(self, basename)


        ''' Create ParSen class
            
        Parameters
        ---------- 
        jco_df : DataFrame, optional,
            Pandas DataFrame of the jacobian. If not provided then it will be
            read in based on base name of pest file provided. Providing a jco_df
            offers some efficiencies if working interactively. Otherwise the jco
            is read in every time ParSen class is initialized.  Jco_df is an
            attribute of the Jco class

        drop_regul: {False, True}, optional
            Flag to drop regularization information in calculating parameter
            sensitivity.  Will set weight to zero for all observations with
            'regul' in the observation group name
        
        drop_groups: list, optional
            List of observation groups to drop when calculating parameter 
            sensitivity.  If all groups are part of regularization it may
            be easier to use the drop_regul flag
            
        keep_groups: list, optional
            List of observation groups to include in calculating parameter
            sensitivity.  Sometimes easier to use when looking at sensitivity
            to a single, or small number, or observation groups
        
        keep_obs: list, optional
            List of obervations to include in calculating parameter
            sensitivity.  If keep_obs != None then weights for all observations
            not in keep_obs will be set to zero.
            
        remove_obs: list, optional
            List of obervations to remove in calculating parameter
            sensitivity.  If remove_obs != None then weights for all observations
            in remove_obs will be set to zero.       
            
        Attributes
        ----------
        df : Pandas DataFrame 
            DataFrame of parameter sensitivity.  Index entries of the DataFrame
            are the parameter names.  The DataFrame has two columns: 
            1) Parameter Group and 2) Sensitivity
            
        Methods
        -------
        plot()
        tail()
        head()
        par()
        group()
        sum_group()
        plot_sum_group()
        plot_mean_group()



        Notes
        ------
        For drop_regul = True could alternatively remove regularization info 
        from jco_df but haven't found easy way to do so, particularly 
        with large jco
        
        ''' 
        if jco_df == None:              
            jco_df = self._load_jco()
        self._read_par_data()
        self._read_obs_data()
        
        # Build obs dictionary
        # key is OBSNME values are (WEIGHT, OBGNME)
        obs_dict = {}
        for index, row in self.obsdata.iterrows():
            obs_dict[index.lower()] = (row['WEIGHT'], row['OBGNME'].lower())
        # Also need to get prior info if present
        try:
            self._read_prior()
            for index, row in self.priordata.iterrows():
                obs_dict[index.lower()] = (row['WEIGHT'], row['OBGNME'].lower())
        except:
            pass
        # Build pars_dict
        # key is PARNME value is PARGP
        pars_dict = {}
        for index, row in self.pardata.iterrows():
            pars_dict[index.lower()] = row['PARGP'].lower()
        

        # Build weights array
        weights = []
        ob_groups = []
        
        for ob in jco_df.index:
            weight = float(obs_dict[ob][0])
            ob_group = obs_dict[ob][1]
            
            # Set weights for regularization info to zero if drop_regul == True
            if drop_regul == True and 'regul' in ob_group.lower():
                weight = 0.0
            
            # Set weights for obs in drop_groups to zero
            if drop_groups != None:
                # set all groups in drop_groups to lower case
                drop_groups = [item.lower() for item in drop_groups]
                if ob_group.lower() in drop_groups:
                    weight = 0.0
            
            # Set weights for obs not in keep_group to zero
            if keep_groups != None:
                # set all groups in keep_groups to lower case
                keep_groups = [item.lower() for item in keep_groups]
                if ob_group.lower() not in keep_groups:
                    weight = 0.0
                    
            # Set weights for obs not in keep_obs to zero
            if keep_obs != None:
                # set all obs in keep_obs to lower case
                keep_obs = [item.lower() for item in keep_obs]
                if ob.lower() not in keep_obs:
                    weight = 0.0
            # Set weights for obs in remove_obs to zero
            if remove_obs != None:
                # set all obs in keep_obs to lower case
                remove_obs = [item.lower() for item in remove_obs]
                if ob.lower() in remove_obs:
                    weight = 0.0                
                
            weights.append(weight)
            ob_groups.append(ob_group)
        
        # Get count of non-zero weights    
        n_nonzero_weights = np.count_nonzero(weights)
        
        # Calculate sensitivities
        sensitivities = []
        for col in jco_df:
            sen = np.linalg.norm(np.asarray(jco_df[col])*weights)/n_nonzero_weights
            sensitivities.append(sen)    
        
        # Build Group Array
        par_groups = []
        for par in jco_df.columns:
            par_group = pars_dict[par]
            par_groups.append(par_group)
        
        # Build pandas data frame of parameter sensitivities    
        sen_data = {'Sensitivity' : sensitivities, 'Parameter Group' : par_groups}
        df = pd.DataFrame(sen_data, index = jco_df.columns)
        self.df = df


            
    def tail(self, n_tail):
        ''' Get the lest sensitive parameters
        Parameters
        ----------
        n_tail: int
            Number of parameters to get
                
        Returns
        ---------
        pandas Series
            Series of n_tail least sensitive parameters
                
        '''
        return self.df.sort(columns = 'Sensitivity', ascending = False)\
        .tail(n=n_tail)['Sensitivity']
        
    def head(self, n_head):
        ''' Get the most sensitive parameters
        Parameters
        ----------
        n_head: int
            Number of parameters to get
                
        Returns
        -------
        pandas Series
            Series of n_head most sensitive parameters
        '''
        return self.df.sort(columns = 'Sensitivity', ascending = False)\
        .head(n=n_head)['Sensitivity']

    def par(self, parameter):
        '''Return the sensitivity of a single parameter
        
        Parameters
        ----------
        parameter: string
        
        Returns
        ---------
        float
            sensitivity of parameter
        
        '''
        return self.df.xs(parameter)['Sensitivity']
        
    def group(self, group, n = None):
        '''Return the sensitivites of a parameter group
        
        Parameters
        ----------
        group: string
        
        n: {None, int}, optional
            If None then return all parmeters from group, else n is the number
            of paremeters to return.
            If n is less than 0 then return the least sensitive parameters 
            If n is greater than 0 then retrun the most sensitive parameters
            
        Returns
        -------
        Pandas DataFrame
        
        '''
        group = group.lower()
        if n == None:
            n_head = len(self.df.index)
        else:
            n_head = n
        
        if n_head > 0:            
            sensitivity = self.df.sort(columns = 'Sensitivity', 
                                               ascending = False)\
                                               .ix[self.df['Parameter Group'] == group].head(n=n_head)
        if n_head < 0:
            n_head = abs(n_head)            
            sensitivity = self.df.sort(columns = 'Sensitivity', 
                                               ascending = False)\
                                               .ix[self.df['Parameter Group'] == group].tail(n=n_head)
            
        sensitivity.index.name = 'Parameter'
        return sensitivity
        
    def sum_group (self):
        ''' Return sum of all parameters sensitivity by group
        
        Returns
        -------
        Pandas DataFrame
        '''
        sen_grouped = self.df.groupby(['Parameter Group'])\
        .aggregate(np.sum).sort(columns = 'Sensitivity', ascending = False)
        return sen_grouped

        
    def plot(self, n = None, group = None, color_dict = None, alt_labels = None, **kwds):
        if n == None:
            n_head = len(self.df.index)
        else:
            n_head = n

        if group == None:    

            if n_head > 0:                        
                sensitivity = self.df.sort(columns = 'Sensitivity', ascending = False).head(n=n_head)
            if n_head < 0:
                n_head = abs(n_head)
                sensitivity = self.df.sort(columns = 'Sensitivity', ascending = False).tail(n=n_head)

        if group != None:
            group = group.lower()           
            if n_head > 0:            
                
                sensitivity = self.df.sort(columns = 'Sensitivity', ascending = False).ix[self.df['Parameter Group'] == group].head(n=n_head)         
            if n_head < 0:
                n_head = abs(n_head)            
                sensitivity = self.df.sort(columns = 'Sensitivity', ascending = False).ix[self.df['Parameter Group'] == group].tail(n=n_head)

        if 'ylabel' not in kwds:
            kwds['ylabel'] = 'Parameter Sensitivity'
        if 'xlabel' not in kwds:
            kwds['xlabel'] = 'Parameter'                   

        plot_obj = plots.BarPloth(sensitivity, values_col = 'Sensitivity',
                                  group_col = 'Parameter Group', color_dict = color_dict, alt_labels = alt_labels, **kwds)
        plot_obj.generate()
        plot_obj.draw()

        return plot_obj.fig, plot_obj.ax
        
    def plot_mean_group (self, alt_labels = None, **kwds):
        ''' Plot mean of all parameters sensitivity by group
        
        Returns
        -------
        Matplotlib plot
            Bar plot of mean of sensitivity by parameter group
        '''
        sen_grouped = self.df.groupby(['Parameter Group']).aggregate(np.mean).sort(columns = 'Sensitivity', ascending = False)
        
        if 'ylabel' not in kwds:
            kwds['ylabel'] = 'Mean of Parameter Sensitivity'
        if 'xlabel' not in kwds:
            kwds['xlabel'] = 'Parameter Group'

        plot_obj = plots.BarPloth(sen_grouped, values_col = 'Sensitivity', alt_labels = alt_labels, **kwds)
        plot_obj.generate()
        plot_obj.draw()

        return plot_obj.fig, plot_obj.ax
        
    def plot_sum_group (self, alt_labels = None, **kwds):
        ''' Plot sum of all parameters sensitivity by group
        
        Returns
        -------
        Matplotlib plot
            Bar plot of sum of sensitivity by parameter group
        '''

        sen_grouped = self.df.groupby(['Parameter Group'])\
        .aggregate(np.sum).sort(columns = 'Sensitivity', ascending = False)
        
        if 'ylabel' not in kwds:
            kwds['ylabel'] = 'Sum of Parameter Sensitivity'
        if 'xlabel' not in kwds:
            kwds['xlabel'] = 'Parameter Group'
        
        
        plot_obj = plots.BarPloth(sen_grouped, values_col = 'Sensitivity', alt_labels = alt_labels, **kwds)
        plot_obj.generate()
        plot_obj.draw()

        return plot_obj.fig, plot_obj.ax
        


        
        
if __name__ == '__main__':
    parsen = ParSen(r'C:\Users\egc\pest_tools-1\cc\columbia')
    #pst = Pest(r'C:\Users\egc\pest_tools-1\cc\columbia')
    alt_labels = {'r_lc' : "Full Parameter Description 'r_lc'"}
    color_dict = {'kz': (0.89411765336990356, 0.10196078568696976, 0.10980392247438431, 1.0),
                  'kp': 'g',
                  'sfr_cond' : 'b',
                  'rech' : 'k'}
    parsen.plot(n=20)
#    parsen.plot(n=20, color_dict = color_dict, alt_labels = alt_labels)
#    parsen.plot_mean_group(color = 'k')
#    parsen.plot(n=-20)
#    parsen.plot(n=20, group = 'kz')
#    parsen.plot_mean_group()
#    parsen.plot_sum_group()
    #parsen.plot(n=20, cmap = 'Set3')